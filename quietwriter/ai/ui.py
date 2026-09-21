from __future__ import annotations
import html
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QTextCursor, QTextDocument, QIcon, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QTextEdit, QTextBrowser, QMessageBox, QApplication
)
from .providers import ProviderFactory
from .context import ContextBuilder
from .conversations import ConversationStore
from ..themes import THEMES


class ProviderChatWorker(QThread):
    token = Signal(str)
    thinking = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, provider, model: str, messages: list[dict], options=None):
        super().__init__()
        self.provider = provider
        self.model = model
        self.messages = messages
        self.options = options or {}
        self._stop = False

    def stop(self):
        self._stop = True
        try:
            self.provider.cancel_active()
        except Exception:
            pass

    def run(self):
        try:
            for chunk in self.provider.stream_chat(self.model, self.messages, **self.options):
                if self._stop:
                    self.cancelled.emit(); return
                if chunk.thinking: self.thinking.emit(chunk.thinking)
                if chunk.content: self.token.emit(chunk.content)
            if self._stop:
                self.cancelled.emit()
            else:
                self.finished_ok.emit()
        except Exception as exc:
            if self._stop:
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))



def markdown_to_html(text: str) -> str:
    doc = QTextDocument()
    doc.setMarkdown(text or '')
    return doc.toHtml()


class AIPanel(QWidget):
    """Provider-onafhankelijk AI-paneel met veilige worker-lifecycle."""
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.worker = None
        self.current_assistant = ''
        self._thinking_dots = 0
        self._thinking_base = 'Denken'
        self._final_started = False
        self._thinking_text = ''
        self._active_context = None
        self._active_user_index = None
        self.messages: list[dict] = []
        self.store = None

        self.thinking_timer = QTimer(self); self.thinking_timer.setInterval(350); self.thinking_timer.timeout.connect(self._animate_thinking)
        self.render_timer = QTimer(self); self.render_timer.setSingleShot(True); self.render_timer.setInterval(70); self.render_timer.timeout.connect(lambda: self._render_chat(streaming_placeholder=True))
        lay = QVBoxLayout(self); lay.setContentsMargins(14,14,14,14); lay.setSpacing(8)

        top = QHBoxLayout()
        lab = QLabel('AI-assistent'); lab.setObjectName('sectionTitle')
        self.context = QComboBox(); self.context.addItems(['Huidig hoofdstuk', 'Huidige sectie', 'Hele boek'])
        top.addWidget(lab); top.addStretch(); top.addWidget(self.context)
        lay.addLayout(top)


        self.context_summary = QLabel('Schrijverspersona · Huidig hoofdstuk')
        self.context_summary.setObjectName('muted'); self.context_summary.setWordWrap(True)
        lay.addWidget(self.context_summary)

        context_row = QHBoxLayout()
        self.context_button = QPushButton('Context bekijken'); self.context_button.clicked.connect(self._toggle_context_details)
        self.clear_button = QPushButton('Nieuw gesprek'); self.clear_button.clicked.connect(self.clear_conversation)
        context_row.addWidget(self.context_button); context_row.addStretch(); context_row.addWidget(self.clear_button)
        lay.addLayout(context_row)

        self.context_details = QTextEdit(); self.context_details.setReadOnly(True); self.context_details.setMaximumHeight(120); self.context_details.hide()
        lay.addWidget(self.context_details)

        self.thinking_button = QPushButton('Denken…'); self.thinking_button.setObjectName('thinkingButton'); self.thinking_button.clicked.connect(self._toggle_thinking_details); self.thinking_button.hide()
        self.thinking_details = QTextEdit(); self.thinking_details.setReadOnly(True); self.thinking_details.setMaximumHeight(130); self.thinking_details.setObjectName('thinkingDetails'); self.thinking_details.hide()
        lay.addWidget(self.thinking_button, 0, Qt.AlignLeft); lay.addWidget(self.thinking_details)

        self.chat = QTextBrowser(); self.chat.setObjectName('aiChat'); self.chat.setOpenExternalLinks(True)
        self.input = QTextEdit(); self.input.setObjectName('aiInput'); self.input.setMaximumHeight(108); self.input.setPlaceholderText('Stel een vraag over je tekst…')
        self.action_button = QPushButton(); self.action_button.setObjectName('aiActionButton')
        self.action_button.setFixedSize(38, 38)
        self.action_button.clicked.connect(self._action_clicked)
        self._set_action_state(False)
        compose = QHBoxLayout(); compose.setContentsMargins(0,0,0,0); compose.setSpacing(8)
        compose.addWidget(self.input, 1); compose.addWidget(self.action_button, 0, Qt.AlignBottom)
        lay.addWidget(self.chat, 1); lay.addLayout(compose)

    def is_busy(self) -> bool:
        return bool(self.worker and self.worker.isRunning())

    def _icon_path(self, name: str):
        from pathlib import Path
        return str(Path(__file__).resolve().parents[1] / 'icons' / f'{name}.svg')

    def _set_action_state(self, busy: bool):
        self.action_button.setIcon(QIcon(self._icon_path('stop' if busy else 'send')))
        self.action_button.setToolTip('Stop AI' if busy else 'Versturen')
        self.action_button.setAccessibleName('Stop AI' if busy else 'Versturen')

    def _action_clicked(self):
        if self.is_busy():
            self.stop_ai()
        else:
            self.send()

    def _update_busy_buttons(self):
        busy=self.is_busy()
        self.action_button.setEnabled(True)
        self._set_action_state(busy)
        self.clear_button.setEnabled(not busy)

    def set_book(self, book):
        if self.is_busy():
            self.stop_ai()
            self._wait_for_workers(2500)
        self.store = ConversationStore(book) if book else None
        self.messages = self.store.load() if self.store else []
        self._render_chat()

    def clear_conversation(self):
        if self.is_busy(): return
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
        if not prompt or self.is_busy(): return
        provider, model = self._provider_model()
        if not model:
            QMessageBox.information(self, 'AI', 'Kies eerst een AI-model in Instellingen.'); return
        if not provider.is_available():
            QMessageBox.warning(self, 'AI', 'De geselecteerde AI-provider is niet bereikbaar of niet geconfigureerd.'); return

        builder = ContextBuilder(self.main)
        manuscript_context = builder.build(self.context.currentText())
        self.input.clear()
        self._continue_send(provider, model, prompt, manuscript_context)


    def _continue_send(self, provider, model: str, prompt: str, context):
        self._active_context = context
        self.context_summary.setText(' · '.join(context.pieces))
        lines=[f'Context: {x}' for x in context.pieces]
        self.context_details.setPlainText('\n'.join(lines))
        persona=self.main.library.read_persona()
        context_text=context.text

        def build_system(ctx_text: str) -> str:
            return (
                'Je bent de schrijf- en redactieassistent van de gebruiker. Beantwoord precies de concrete opdracht. '
                'Gebruik ALTIJD het schrijversprofiel als stijl- en beoordelingskader, maar genereer of herschrijf alleen tekst als daarom wordt gevraagd. '
                'Pas nooit rechtstreeks manuscriptbestanden aan; geef wijzigingen alleen in je antwoord. '
                'Als informatie ontbreekt, zeg dat expliciet.\n\n'
                f'SCHRIJVERSPROFIEL:\n{persona}\n\nCONTEXT ({context.label}):\n{ctx_text}'
            )

        self.messages.append(ConversationStore.entry('user', prompt, {'pieces': context.pieces, 'scope': self.context.currentText()}))
        self._active_user_index=len(self.messages)-1
        self.current_assistant=''; self._final_started=False; self._thinking_text=''
        self._render_chat(streaming_placeholder=True); self._start_thinking('Denken')

        # Eenvoudige, directe chatflow. Geen tokenberekeningen, geen automatische
        # contextvensters en geen provider-specifieke tuning. QuietWriter stuurt
        # alleen persona + gekozen manuscriptcontext + een beperkte recente chat
        # naar het geselecteerde model. De provider/modelruntime bepaalt de context.
        recent=[{'role':m['role'],'content':m['content']} for m in self.messages[-6:] if m.get('role') in {'user','assistant'}]
        messages=[{'role':'system','content':build_system(context_text)}] + recent
        self.worker=ProviderChatWorker(provider,model,messages,options={})
        self.worker.token.connect(self._token); self.worker.thinking.connect(self._thinking)
        self.worker.failed.connect(self._fail); self.worker.finished_ok.connect(self._done)
        self.worker.cancelled.connect(self._chat_cancelled); self.worker.finished.connect(self._chat_thread_finished)
        self.worker.start(); self._update_busy_buttons()

    def stop_ai(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.action_button.setEnabled(False)
            self._thinking_base = 'Stoppen'
            self.thinking_button.setText('Stoppen…')

    def _wait_for_workers(self, timeout_ms=3000) -> bool:
        if not self.worker or not self.worker.isRunning():
            return True
        return self.worker.wait(timeout_ms)

    def shutdown(self, timeout_ms=4000) -> bool:
        self.stop_ai()
        return self._wait_for_workers(timeout_ms)

    def _start_thinking(self, base='Denken'):
        self._thinking_base=base; self._thinking_dots = 0
        self.thinking_details.clear(); self.thinking_details.hide()
        self.thinking_button.setText(base+'…'); self.thinking_button.show(); self.thinking_timer.start()

    def _animate_thinking(self):
        self._thinking_dots = (self._thinking_dots + 1) % 4
        self.thinking_button.setText(self._thinking_base + '.' * (self._thinking_dots + 1))

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
            self.messages.append(ConversationStore.entry('assistant', self.current_assistant, {'pieces': context.pieces if context else []}))
            if self.store: self.store.save(self.messages)
        self._active_user_index=None
        self.render_timer.stop(); self.current_assistant = ''; self._render_chat()

    def _fail(self, err):
        self._finish_thinking(); self.current_assistant=''
        self.messages.append(ConversationStore.entry('assistant', f'Fout: {err}'))
        self._active_user_index=None
        if self.store: self.store.save(self.messages)
        self._render_chat()

    def _chat_cancelled(self):
        self._finish_thinking(); self.render_timer.stop(); self.current_assistant=''
        # Een gestopte opdracht wordt niet als half gesprek bewaard.
        if self._active_user_index is not None and self._active_user_index == len(self.messages)-1:
            if self.messages[self._active_user_index].get('role') == 'user':
                self.messages.pop()
        self._active_user_index=None
        self.context_summary.setText('AI gestopt.')
        self._render_chat()

    def _chat_thread_finished(self):
        obj=self.worker
        self.worker=None
        if obj is not None: obj.deleteLater()
        self._update_busy_buttons()

    def _render_chat(self, streaming_placeholder=False):
        theme = THEMES.get(str(self.main.settings.value('theme','Helder')), THEMES['Helder'])
        user_bg = theme['accent_soft']
        ai_bg = theme['panel2']
        text = theme['text']
        muted = theme['muted']
        blocks=[]
        for msg in self.messages:
            role = msg.get('role'); content = msg.get('content','')
            if role == 'user':
                body = html.escape(content).replace('\n','<br>')
                blocks.append(
                    f'<div align="right"><table width="86%" cellspacing="0" cellpadding="10" bgcolor="{user_bg}">'
                    f'<tr><td><font color="{muted}" size="2"><b>JIJ</b></font><br><font color="{text}">{body}</font></td></tr></table></div><br>'
                )
            else:
                body = markdown_to_html(content)
                blocks.append(
                    f'<div align="left"><table width="96%" cellspacing="0" cellpadding="10" bgcolor="{ai_bg}">'
                    f'<tr><td><font color="{muted}" size="2"><b>QUIETWRITER</b></font><br>{body}</td></tr></table></div><br>'
                )
        if streaming_placeholder and self.current_assistant:
            body = markdown_to_html(self.current_assistant)
            blocks.append(
                f'<div align="left"><table width="96%" cellspacing="0" cellpadding="10" bgcolor="{ai_bg}">'
                f'<tr><td><font color="{muted}" size="2"><b>QUIETWRITER</b></font><br>{body}</td></tr></table></div><br>'
            )
        self.chat.setHtml('<html><body style="margin:4px;">' + ''.join(blocks) + '</body></html>')
        cur=self.chat.textCursor(); cur.movePosition(QTextCursor.End); self.chat.setTextCursor(cur)

