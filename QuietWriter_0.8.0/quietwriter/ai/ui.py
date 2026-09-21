from __future__ import annotations
import html
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTextEdit, QMessageBox, QFrame
)
from .providers import ProviderFactory
from .context import ContextBuilder
from .conversations import ConversationStore
from .embedding_cache import EmbeddingCache, cosine


class ProviderChatWorker(QThread):
    token = Signal(str)
    thinking = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(self, provider, model: str, messages: list[dict], options=None):
        super().__init__()
        self.provider = provider
        self.model = model
        self.messages = messages
        self.options = options or {}
        self._stop = False

    def stop(self): self._stop = True

    def run(self):
        try:
            for chunk in self.provider.stream_chat(self.model, self.messages, **self.options):
                if self._stop: return
                if chunk.thinking: self.thinking.emit(chunk.thinking)
                if chunk.content: self.token.emit(chunk.content)
            self.finished_ok.emit()
        except Exception as exc:
            self.failed.emit(str(exc))




class LibrarianWorker(QThread):
    ranked = Signal(object)
    failed = Signal(str)

    def __init__(self, prompt: str, catalog: list[dict], lexical: list[dict],
                 fast_provider=None, fast_model: str = '', embedding_provider=None,
                 embedding_model: str = '', cache_path=None):
        super().__init__()
        self.prompt=prompt; self.catalog=catalog; self.lexical=lexical
        self.fast_provider=fast_provider; self.fast_model=fast_model
        self.embedding_provider=embedding_provider; self.embedding_model=embedding_model
        self.cache_path=cache_path

    @staticmethod
    def _compact(c):
        return ('Titel: '+str(c.get('title',''))+'\nTags: '+str(c.get('tags',''))+
                '\nBeschrijving: '+str(c.get('description',''))[:240]+
                '\nSynopsis: '+str(c.get('synopsis',''))[:480])

    def _semantic(self):
        if not (self.embedding_provider and self.embedding_model and self.cache_path): return []
        cache=EmbeddingCache(self.cache_path)
        try:
            qv=self.embedding_provider.embed(self.embedding_model,[self.prompt])
            if not qv: return []
            qv=qv[0]; missing=[]; vectors={}
            for row in self.catalog:
                v=cache.get(str(row.get('path','')),self.embedding_model,float(row.get('mtime',0) or 0))
                if v is None: missing.append(row)
                else: vectors[str(row.get('path',''))]=v
            for offset in range(0,len(missing),16):
                batch=missing[offset:offset+16]
                vals=self.embedding_provider.embed(self.embedding_model,[self._compact(x) for x in batch])
                for row,v in zip(batch,vals):
                    key=str(row.get('path','')); vectors[key]=v; cache.put(key,self.embedding_model,float(row.get('mtime',0) or 0),v)
            scored=[]
            for row in self.catalog:
                v=vectors.get(str(row.get('path','')))
                if v: scored.append((cosine(qv,v),row))
            scored.sort(key=lambda x:x[0], reverse=True)
            return [row for _,row in scored[:20]]
        finally:
            cache.close()

    def _choose_with_fast_model(self, rows):
        import json, re
        if not (self.fast_provider and self.fast_model): return []
        system=('Je bent uitsluitend bibliothecaris. Kies de verhalen die inhoudelijk het meest relevant zijn voor de vraag. '
                'Let op titel, tags, beschrijving en synopsis. Antwoord ALLEEN met een JSON-array van maximaal 5 numerieke id’s.')
        catalog=[]
        for i,c in enumerate(rows,1):
            catalog.append({'id':i,'title':c.get('title',''),'tags':c.get('tags',''),
                            'description':str(c.get('description',''))[:220], 'synopsis':str(c.get('synopsis',''))[:420]})
        raw=self.fast_provider.complete(self.fast_model,[{'role':'system','content':system},
            {'role':'user','content':f'Vraag: {self.prompt}\n\nCatalogus:\n{json.dumps(catalog, ensure_ascii=False)}'}],temperature=0.0)
        m=re.search(r'\[[^\]]*\]',raw,re.S); ids=json.loads(m.group(0)) if m else []
        return [rows[i-1] for i in ids if isinstance(i,int) and 1<=i<=len(rows)][:5]

    def run(self):
        try:
            semantic=[]
            try: semantic=self._semantic()
            except Exception: semantic=[]
            # Dedup pool: lexical matches first, then semantic neighbours.
            pool=[]; seen=set()
            for row in list(self.lexical)+semantic:
                key=str(row.get('path',''))
                if key and key not in seen: seen.add(key); pool.append(row)
            if not pool: pool=list(self.catalog)[:20]

            if self.fast_provider and self.fast_model:
                # Als er geen embeddingmodel is, leest het kleine model de hele compacte
                # bibliotheek in batches. Met embeddings hoeft alleen de sterke pool te worden gererankt.
                source=pool if semantic else self.catalog
                winners=[]
                for offset in range(0,len(source),40):
                    batch=source[offset:offset+40]
                    winners.extend(self._choose_with_fast_model(batch) or batch[:2])
                if len(winners)>5: winners=self._choose_with_fast_model(winners) or winners[:5]
                self.ranked.emit(winners[:5]); return
            self.ranked.emit(pool[:5])
        except Exception as exc:
            self.failed.emit(str(exc))


def markdown_to_html(text: str) -> str:
    doc = QTextDocument()
    doc.setMarkdown(text or '')
    return doc.toHtml()


class AIPanel(QWidget):
    """Provider-onafhankelijk AI-paneel.

    Het paneel kent alleen de provider-interface. Ollama/OpenRouter-specifieke code
    staat in quietwriter.ai.*_provider.py.
    """
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.worker = None
        self.librarian = None
        self.current_assistant = ''
        self._thinking_dots = 0
        self._final_started = False
        self._thinking_text = ''
        self._active_context = None
        self.messages: list[dict] = []
        self.store = None

        self.thinking_timer = QTimer(self); self.thinking_timer.setInterval(350); self.thinking_timer.timeout.connect(self._animate_thinking)
        self.render_timer = QTimer(self); self.render_timer.setSingleShot(True); self.render_timer.setInterval(70); self.render_timer.timeout.connect(lambda: self._render_chat(streaming_placeholder=True))
        lay = QVBoxLayout(self); lay.setContentsMargins(14,14,14,14); lay.setSpacing(8)

        top = QHBoxLayout()
        lab = QLabel('AI-assistent'); lab.setObjectName('sectionTitle')
        self.context = QComboBox(); self.context.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek', 'Verhalenbibliotheek'])
        top.addWidget(lab); top.addStretch(); top.addWidget(self.context)
        lay.addLayout(top)

        self.context_summary = QLabel('Schrijverspersona · Huidig hoofdstuk')
        self.context_summary.setObjectName('muted'); self.context_summary.setWordWrap(True)
        lay.addWidget(self.context_summary)

        context_row = QHBoxLayout()
        self.context_button = QPushButton('Context bekijken')
        self.context_button.clicked.connect(self._toggle_context_details)
        self.clear_button = QPushButton('Nieuw gesprek')
        self.clear_button.clicked.connect(self.clear_conversation)
        context_row.addWidget(self.context_button); context_row.addStretch(); context_row.addWidget(self.clear_button)
        lay.addLayout(context_row)

        self.context_details = QTextEdit(); self.context_details.setReadOnly(True); self.context_details.setMaximumHeight(120); self.context_details.hide()
        lay.addWidget(self.context_details)

        self.thinking_button = QPushButton('Denken…'); self.thinking_button.setObjectName('thinkingButton'); self.thinking_button.clicked.connect(self._toggle_thinking_details); self.thinking_button.hide()
        self.thinking_details = QTextEdit(); self.thinking_details.setReadOnly(True); self.thinking_details.setMaximumHeight(130); self.thinking_details.setObjectName('thinkingDetails'); self.thinking_details.hide()
        lay.addWidget(self.thinking_button, 0, Qt.AlignLeft); lay.addWidget(self.thinking_details)

        self.chat = QTextEdit(); self.chat.setReadOnly(True); self.chat.setOpenExternalLinks(True)
        self.input = QTextEdit(); self.input.setMaximumHeight(120); self.input.setPlaceholderText('Typ een opdracht…')
        self.send_button = QPushButton('Versturen'); self.send_button.clicked.connect(self.send)
        lay.addWidget(self.chat, 1); lay.addWidget(self.input); lay.addWidget(self.send_button, 0, Qt.AlignRight)

    def set_book(self, book):
        self.store = ConversationStore(book) if book else None
        self.messages = self.store.load() if self.store else []
        self._render_chat()

    def clear_conversation(self):
        if self.worker: return
        self.messages = []
        if self.store: self.store.save(self.messages)
        self._render_chat()

    def _provider_model(self):
        provider = ProviderFactory.from_settings(self.main.settings)
        pname = str(self.main.settings.value('ai_provider', 'ollama') or 'ollama').lower()
        key = 'openrouter_model' if pname == 'openrouter' else 'ollama_model'
        return provider, str(self.main.settings.value(key, '') or '')

    def send(self):
        prompt = self.input.toPlainText().strip()
        if not prompt or self.worker: return
        provider, model = self._provider_model()
        if not model:
            QMessageBox.information(self, 'AI', 'Kies eerst een AI-model in Instellingen.')
            return
        if not provider.is_available():
            QMessageBox.warning(self, 'AI', 'De geselecteerde AI-provider is niet bereikbaar of niet geconfigureerd.')
            return

        builder = ContextBuilder(self.main, provider)
        if self.context.currentText() == 'Verhalenbibliotheek':
            lexical = builder._library_sources(prompt, 18)
            catalog = self.main.story_index.list_all()
            fast_model = str(self.main.settings.value('fast_model', '') or '')
            embedding_model = str(self.main.settings.value('embedding_model', '') or '')
            local_provider = ProviderFactory.for_name(self.main.settings, 'ollama')
            local_ok = local_provider.is_available()
            if catalog and ((fast_model and local_ok) or (embedding_model and local_ok)):
                self.input.clear(); self.current_assistant=''; self._final_started=False; self._thinking_text=''
                self._start_thinking(); self.thinking_button.setText('Verhalen selecteren…')
                self.librarian = LibrarianWorker(prompt, catalog, lexical,
                    fast_provider=local_provider if fast_model and local_ok else None, fast_model=fast_model,
                    embedding_provider=local_provider if embedding_model and local_ok else None, embedding_model=embedding_model,
                    cache_path=self.main.library.cache_dir / 'story_embeddings.db')
                self.librarian.ranked.connect(lambda rows: self._continue_send(provider, model, prompt, builder.library_bundle_from_rows(rows, 5)))
                self.librarian.failed.connect(lambda _err: self._continue_send(provider, model, prompt, builder.library_bundle_from_rows(lexical[:5], 5)))
                self.librarian.start(); return
            context = builder.library_bundle_from_rows(lexical[:5], 5)
        else:
            context = builder.build(self.context.currentText(), prompt)
        self._continue_send(provider, model, prompt, context)

    def _continue_send(self, provider, model: str, prompt: str, context):
        self.librarian = None
        self._active_context = context
        self.context_summary.setText(' · '.join(context.pieces))
        lines=[f'Context: {x}' for x in context.pieces]
        if context.sources:
            lines += ['', 'Geraadpleegde verhalen:']
            lines += [f"• {x['title']}" + (f" — {x['tags']}" if x.get('tags') else '') for x in context.sources]
        self.context_details.setPlainText('\n'.join(lines))
        persona=self.main.library.read_persona()
        max_chars=int(self.main.settings.value('ai_context_chars', 90000) or 90000)
        context_text=context.text
        if len(context_text)>max_chars:
            context_text=context_text[:max_chars]+'\n\n[… context ingekort; verhoog de contextlimiet in Instellingen indien nodig …]'
        system=('Je bent de schrijf- en redactieassistent van de gebruiker. Gebruik ALTIJD het onderstaande schrijversprofiel als vaste persona. '
                'Pas nooit rechtstreeks manuscriptbestanden aan. Geef wijzigingen, herschrijvingen en suggesties uitsluitend in je antwoord. '
                'Wanneer informatie ontbreekt, zeg dat expliciet.\n\n'
                f'SCHRIJVERSPROFIEL:\n{persona}\n\nCONTEXT ({context.label}):\n{context_text}')
        self.messages.append(ConversationStore.entry('user',prompt,{'pieces':context.pieces,'sources':context.sources,'scope':self.context.currentText()}))
        self.input.clear(); self.current_assistant=''; self._final_started=False; self._thinking_text=''
        self._render_chat(streaming_placeholder=True); self._start_thinking()
        recent=[{'role':m['role'],'content':m['content']} for m in self.messages[-12:] if m.get('role') in {'user','assistant'}]
        messages=[{'role':'system','content':system}]+recent
        self.worker=ProviderChatWorker(provider,model,messages,options={'temperature':0.65})
        self.worker.token.connect(self._token); self.worker.thinking.connect(self._thinking); self.worker.failed.connect(self._fail); self.worker.finished_ok.connect(self._done); self.worker.start()

    def _start_thinking(self):
        self._thinking_dots = 0; self.thinking_details.clear(); self.thinking_details.hide(); self.thinking_button.setText('Denken…'); self.thinking_button.show(); self.thinking_timer.start()

    def _animate_thinking(self):
        self._thinking_dots = (self._thinking_dots + 1) % 4
        self.thinking_button.setText('Denken' + '.' * (self._thinking_dots + 1))

    def _toggle_thinking_details(self):
        if self._thinking_text.strip(): self.thinking_details.setVisible(not self.thinking_details.isVisible())

    def _toggle_context_details(self):
        self.context_details.setVisible(not self.context_details.isVisible())

    def _thinking(self, text):
        self._thinking_text += text
        self.thinking_details.setPlainText(self._thinking_text)
        cur = self.thinking_details.textCursor(); cur.movePosition(QTextCursor.End); self.thinking_details.setTextCursor(cur)

    def _finish_thinking(self):
        self.thinking_timer.stop(); self.thinking_details.clear(); self.thinking_details.hide(); self.thinking_button.hide(); self._thinking_text = ''

    def _token(self, text):
        if not self._final_started:
            self._final_started = True; self._finish_thinking()
        self.current_assistant += text
        if not self.render_timer.isActive(): self.render_timer.start()

    def _done(self):
        self._finish_thinking()
        if self.current_assistant.strip():
            context = self._active_context
            self.messages.append(ConversationStore.entry('assistant', self.current_assistant, {'pieces': context.pieces if context else [], 'sources': context.sources if context else []}))
            if self.store: self.store.save(self.messages)
        self.render_timer.stop(); self.current_assistant = ''; self.worker = None; self._render_chat()

    def _fail(self, err):
        self._finish_thinking(); self.worker = None
        self.current_assistant = ''
        self.messages.append(ConversationStore.entry('assistant', f'Fout: {err}'))
        if self.store: self.store.save(self.messages)
        self._render_chat()

    def _render_chat(self, streaming_placeholder=False):
        blocks=[]
        for msg in self.messages:
            role = msg.get('role')
            content = msg.get('content','')
            if role == 'user':
                body = html.escape(content).replace('\n','<br>')
                blocks.append(f'<p><b>Jij</b><br>{body}</p>')
            else:
                rendered = markdown_to_html(content)
                blocks.append(f'<p><b>AI</b></p>{rendered}')
                sources = (msg.get('context') or {}).get('sources') or []
                if sources:
                    names = ', '.join(html.escape(s.get('title','')) for s in sources)
                    blocks.append(f'<p style="color:#777;font-size:9pt">Gebruikte verhalen: {names}</p>')
        if streaming_placeholder and self.current_assistant:
            blocks.append('<p><b>AI</b></p>' + markdown_to_html(self.current_assistant))
        self.chat.setHtml('<html><body>' + '<hr>'.join(blocks) + '</body></html>')
        cur=self.chat.textCursor(); cur.movePosition(QTextCursor.End); self.chat.setTextCursor(cur)
