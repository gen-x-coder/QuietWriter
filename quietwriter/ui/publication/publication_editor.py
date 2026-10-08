from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..current_page_stack import CurrentPageStack
from ...publication_models import PublicationData, item_definition
from ...publication_storage import PublicationStore
from ...i18n import tr
from ..manuscript_editor import ManuscriptEditor
from .copyright_page import CopyrightPage
from .contents_page import ContentsPage


class SimpleStructuredPage(QWidget):
    changed = Signal()
    def __init__(self, title: str, fields: list[tuple[str, str]], parent=None):
        super().__init__(parent); self._keys=[]; self._edits={}; self._title=title
        root=QVBoxLayout(self); root.setContentsMargins(42,30,42,30); root.setSpacing(14)
        heading=QLabel(title); heading.setObjectName('title'); root.addWidget(heading)
        form=QFormLayout(); form.setVerticalSpacing(12)
        for key,label in fields:
            edit=QLineEdit(); self._keys.append(key); self._edits[key]=edit; edit.textEdited.connect(lambda *_: self.changed.emit()); form.addRow(label,edit)
        root.addLayout(form); root.addStretch()
        buttons=QHBoxLayout(); buttons.addStretch(); self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); buttons.addWidget(self.save_button); root.addLayout(buttons)

    def set_data(self,data):
        for key in self._keys: self._edits[key].setText(str((data or {}).get(key,'')))
        self.save_button.setEnabled(False)

    def data(self): return {key:self._edits[key].text().strip() for key in self._keys}


class FreeTextPage(QWidget):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent); self.key=None; self.dirty=False; self.corrupt=False; self._clean_text=''
        root=QVBoxLayout(self); root.setContentsMargins(30,24,30,24); root.setSpacing(10)
        top=QHBoxLayout(); self.title=QLabel(''); self.title.setObjectName('title'); top.addWidget(self.title); top.addStretch()
        self.save_button=QPushButton(tr('common.save', 'Opslaan')); self.save_button.setObjectName('primaryButton'); self.save_button.setEnabled(False); top.addWidget(self.save_button); root.addLayout(top)
        self.editor=ManuscriptEditor(settings=settings); self.editor.max_text_width=100000; self.editor.min_side_margin=10; self.editor._update_margins(); root.addWidget(self.editor,1)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(2200)
        self.editor.textChanged.connect(self._changed)

    def _changed(self):
        if self.corrupt:
            return
        if self.editor.source_text() == self._clean_text:
            self.dirty=False; self.save_button.setEnabled(False); self.timer.stop(); return
        self.dirty=True; self.save_button.setEnabled(True); self.timer.start()

    def set_text(self,key,label,text, *, corrupt=False):
        self.timer.stop(); self.key=key; self.title.setText(label); self.corrupt=bool(corrupt)
        self.editor.blockSignals(True)
        if self.corrupt:
            self.editor.setPlainText(tr('publication.text.corrupt', 'Dit publicatiebestand is beschadigd en kan niet als UTF-8 worden gelezen.\n\nOpen Integriteit om het te controleren en zo mogelijk te herstellen.'))
        else:
            self.editor.setPlainText(text)
        self.editor.setReadOnly(self.corrupt); self.editor.blockSignals(False); self._clean_text=self.editor.source_text(); self.dirty=False; self.save_button.setEnabled(False)


class PublicationEditor(QWidget):
    """Editor surface for selected front/back matter items."""

    def __init__(self, editor_page):
        super().__init__(editor_page); self.owner=editor_page; self.main=editor_page.main; self.book=None; self.key=None; self.store=PublicationStore(self.main.library); self.data=PublicationData(); self.structured_dirty=False
        self.stack=CurrentPageStack(); root=QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.addWidget(self.stack)
        self.title_page=SimpleStructuredPage(tr('publication.title_page.title', 'Titelpagina'),[('title',tr('publication.title_page.book_title', 'Boektitel')),('subtitle',tr('publication.title_page.subtitle', 'Subtitel')),('author',tr('publication.title_page.author', 'Auteur / pseudoniem')),('publisher',tr('publication.title_page.publisher', 'Uitgever / imprint'))])
        self.epigraph=SimpleStructuredPage(tr('publication.epigraph.title', 'Epigraaf'),[('quote',tr('publication.epigraph.quote', 'Citaat')),('source',tr('publication.epigraph.source', 'Bron / auteur'))])
        self.copyright=CopyrightPage(); self.contents=ContentsPage(); self.free_text=FreeTextPage(settings=self.main.settings)
        for widget in (self.title_page,self.copyright,self.epigraph,self.contents,self.free_text): self.stack.addWidget(widget)
        self.title_page.save_button.clicked.connect(lambda:self._save_structured('title_page',self.title_page.data()))
        self.epigraph.save_button.clicked.connect(lambda:self._save_structured('epigraph',self.epigraph.data()))
        self.copyright.saveRequested.connect(lambda value:self._save_structured('copyright',value))
        self.contents.saveRequested.connect(lambda value:self._save_structured('contents',value))
        self.title_page.changed.connect(self._mark_structured_dirty); self.epigraph.changed.connect(self._mark_structured_dirty)
        self.copyright.changed.connect(self._mark_structured_dirty); self.contents.changed.connect(self._mark_structured_dirty)
        self.free_text.timer.timeout.connect(self.save_pending)
        self.free_text.save_button.clicked.connect(self.save_pending)

    def set_book(self,book):
        # Re-selecting the same book is part of normal tree navigation. Do not
        # reset key/dirty/data here: open_item() must get the chance to save the
        # item that is currently open before switching to another publication item.
        if self.book is book:
            return True
        if self.book and self.save_pending() is False:
            return False
        self.book=book; self.key=None; self.structured_dirty=False
        if book: self.data=self.store.load(book)
        return True

    def adopt_book(self, book):
        """Replace the backing Book after a coordinated live-book reload.

        Conflict resolution has already decided what survives, so this path must
        not try to save the old object again. Keep the currently selected
        publication item when possible and reload it from the adopted live book.
        """
        current_key = self.key
        self.free_text.timer.stop()
        self.book = book
        self.key = None
        self.structured_dirty = False
        self.data = self.store.load(book) if book else PublicationData()
        if book and current_key:
            self.open_item(current_key)
        return True

    def open_item(self,key):
        if not self.book: return False
        if self.key!=key and self.save_pending() is False: return False
        definition=item_definition(key)
        if not definition: return False
        self.key=key; self.data=self.store.load(self.book)
        kind=definition['kind']
        if key=='title_page': self.title_page.set_data(self.data.title_page); self.stack.setCurrentWidget(self.title_page)
        elif key=='copyright': self.copyright.set_data(self.data.copyright); self.stack.setCurrentWidget(self.copyright)
        elif key=='epigraph': self.epigraph.set_data(self.data.epigraph); self.stack.setCurrentWidget(self.epigraph)
        elif key=='contents': self.contents.set_context(self.book,self.main.library,self.data.contents); self.stack.setCurrentWidget(self.contents)
        elif kind=='text': self.free_text.set_text(key,tr(f'publication.item.{key}', definition['label']),self.store.load_text(self.book,key),corrupt=self.store.text_is_corrupt(self.book,key)); self.stack.setCurrentWidget(self.free_text)
        self.structured_dirty=False
        return True

    def _mark_structured_dirty(self, *args):
        if self.key and item_definition(self.key) and item_definition(self.key)['kind'] != 'text':
            self.structured_dirty=True
            page = self.stack.currentWidget()
            button = getattr(page, 'save_button', None)
            if button is not None:
                button.setEnabled(True)

    def _current_structured_value(self):
        if self.key=='title_page': return self.title_page.data()
        if self.key=='copyright': return self.copyright.data()
        if self.key=='epigraph': return self.epigraph.data()
        if self.key=='contents': return self.contents.data()
        return None

    def _save_structured(self,key,value):
        if not self.book:return False
        setattr(self.data,key,value)
        payload = __import__('json').dumps(self.data.to_dict(), ensure_ascii=False, indent=2)
        def write_current_field(book):
            latest_data = self.store.load(book)
            setattr(latest_data, key, value)
            self.store.save(book, latest_data)
            self.data = latest_data
        result = self.owner.persist_publication_change(
            'publication/publication.json', payload, write_current_field
        )
        if result == 'disk':
            self.book = self.owner.book; self.data = self.store.load(self.book); self.open_item(key)
        elif result == 'mine':
            self.book = self.owner.book; self.structured_dirty=False
            button = getattr(self.stack.currentWidget(), 'save_button', None)
            if button is not None: button.setEnabled(False)
            label = tr(f'publication.item.{key}', item_definition(key)['label'])
            self.main.status.showMessage(tr('publication.saved', '{label} opgeslagen.', label=label),2500)
        return result != 'failed'

    def has_pending_changes(self) -> bool:
        if not self.book or not self.key:
            return False
        definition = item_definition(self.key)
        if not definition:
            return False
        if definition['kind'] == 'text':
            return bool(self.free_text.dirty)
        return bool(self.structured_dirty)

    def save_pending(self):
        if not self.book or not self.key:return True
        definition=item_definition(self.key)
        if not definition:return True
        if definition['kind']!='text':
            if not self.structured_dirty:return True
            value=self._current_structured_value()
            return self._save_structured(self.key,value) if value is not None else True
        if self.free_text.corrupt:
            return True
        if not self.free_text.dirty:return True
        text = self.free_text.editor.source_text()
        result = self.owner.persist_publication_change(
            f'publication/texts/{self.key}.md', text, lambda book: self.store.save_text(book,self.key,text)
        )
        if result == 'mine':
            self.book = self.owner.book; self.free_text._clean_text=self.free_text.editor.source_text(); self.free_text.dirty=False; self.free_text.save_button.setEnabled(False); label=tr(f'publication.item.{self.key}', definition['label']); self.main.status.showMessage(tr('publication.saved', '{label} opgeslagen.', label=label),2200); return True
        if result == 'disk':
            self.book = self.owner.book; self.free_text.set_text(self.key,tr(f'publication.item.{self.key}', definition['label']),self.store.load_text(self.book,self.key)); return True
        return False
