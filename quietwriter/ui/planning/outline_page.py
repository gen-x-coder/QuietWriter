from __future__ import annotations

import copy
import json

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QColor, QDrag, QPainter
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMenu, QPushButton, QScrollArea, QTextEdit, QToolButton, QVBoxLayout, QWidget
)

from ...planning_models import Scene
from ...scene_segments import map_scenes
from ...storage import CorruptSourceError
from ...planning_validation import FuturePlanningFormatError
from ...i18n import tr
from ..dialogs import confirm
from ..page_layout import field_label, section_heading
from .combo_value import editable_combo_value


class SceneDialog(QDialog):
    def __init__(self, parent, scene: Scene, chapters, characters):
        super().__init__(parent); self.scene=scene; self.setWindowTitle(tr('planning.outline.scene_title', 'Scène'))
        screen = QApplication.screenAt(parent.mapToGlobal(parent.rect().center())) if parent else None
        screen = screen or QApplication.primaryScreen()
        if screen:
            bounds = screen.availableGeometry()
            self.resize(min(640, max(340, bounds.width() - 48)),
                        min(560, max(280, bounds.height() - 64)))
        else:
            self.resize(640, 560)
        self.setMinimumSize(340, 280)
        root=QVBoxLayout(self); root.setSpacing(10); self.form_scroll=QScrollArea(); self.form_scroll.setWidgetResizable(True); self.form_scroll.setFrameShape(QFrame.NoFrame); form_host=QWidget(); form=QFormLayout(form_host); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); form.setLabelAlignment(Qt.AlignLeft | Qt.AlignTop); form.setHorizontalSpacing(18); form.setVerticalSpacing(10)
        self.title=QLineEdit(scene.title); self.synopsis=QTextEdit(); self.synopsis.setPlainText(scene.synopsis); self.synopsis.setFixedHeight(90)
        self.chapter=QComboBox(); self.chapter.addItem(tr('planning.outline.loose_idea', 'Los idee'), None)
        for ch in chapters: self.chapter.addItem(ch.title, ch.id)
        idx=self.chapter.findData(scene.chapter_id); self.chapter.setCurrentIndex(max(0,idx))
        self.location=QLineEdit(scene.location); self.status=QComboBox(); self.status.setEditable(False)
        for value, key, label in (
            ('idee', 'planning.status.idea', 'Idee'),
            ('uitgewerkt', 'planning.status.developed', 'Uitgewerkt'),
            ('geschreven', 'planning.status.written', 'Geschreven'),
        ):
            self.status.addItem(tr(key, label), value)
        known_status_index = self.status.findData(scene.status)
        if known_status_index >= 0:
            self.status.setCurrentIndex(known_status_index)
        else:
            # Oude/onbekende statuswaarden blijven leesbaar en selecteerbaar,
            # maar de status is bewust nooit vrije tekst.
            self.status.addItem(scene.status or tr('planning.status.idea', 'Idee'), scene.status or 'idee')
            self.status.setCurrentIndex(self.status.count() - 1)
        form.addRow(self._section_heading(tr('planning.outline.section.main', 'Scènegegevens')))
        form.addRow(field_label(tr('planning.outline.field.title', 'Titel'), min_width=110),self.title); form.addRow(field_label(tr('planning.outline.field.chapter', 'Hoofdstuk'), min_width=110),self.chapter); form.addRow(field_label(tr('planning.outline.field.synopsis', 'Synopsis'), min_width=110),self.synopsis); form.addRow(field_label(tr('planning.outline.field.location', 'Locatie'), min_width=110),self.location); form.addRow(field_label(tr('planning.outline.field.status', 'Status'), min_width=110),self.status)
        self.character_checks=[]; chars=QWidget(); cl=QVBoxLayout(chars); cl.setContentsMargins(0,0,0,0)
        for char in characters:
            cb=QCheckBox(char.name); cb.setProperty('characterId',char.id); cb.setChecked(char.id in scene.character_ids); cl.addWidget(cb); self.character_checks.append(cb)
        if not characters:
            none=QLabel(tr('planning.outline.no_characters', 'Nog geen personages. Je maakt ze aan bij Planning → Personages.')); none.setObjectName('muted'); none.setWordWrap(True); cl.addWidget(none)
        form.addRow(field_label(tr('planning.outline.field.characters', 'Personages'), min_width=110),chars)
        self.goal=self._text(scene.goal); self.conflict=self._text(scene.conflict); self.outcome=self._text(scene.outcome); self.notes=self._text(scene.notes)
        # All fields stay visible; understated headings explain the grouping.
        form.addRow(self._section_heading(tr('planning.outline.section.depth', 'Verdieping')))
        form.addRow(field_label(tr('planning.outline.field.goal', 'Doel'), min_width=110), self.goal)
        form.addRow(field_label(tr('planning.outline.field.conflict', 'Conflict'), min_width=110), self.conflict)
        form.addRow(field_label(tr('planning.outline.field.outcome', 'Uitkomst'), min_width=110), self.outcome)
        form.addRow(field_label(tr('planning.outline.field.notes', 'Notities'), min_width=110), self.notes)
        self.form_scroll.setWidget(form_host); root.addWidget(self.form_scroll,1); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); save_button=buttons.button(QDialogButtonBox.Save); cancel_button=buttons.button(QDialogButtonBox.Cancel); save_button.setText(tr('common.save', 'Opslaan')); cancel_button.setText(tr('common.cancel', 'Annuleren')); save_button.setObjectName('primaryButton'); cancel_button.setObjectName('secondaryButton'); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    @staticmethod
    def _section_heading(text):
        return section_heading(text)
    def _text(self,value):
        e=QTextEdit(); e.setPlainText(value); e.setFixedHeight(108); return e
    def apply(self):
        s=self.scene; s.title=self.title.text().strip() or tr('planning.outline.untitled_scene', 'Naamloze scène'); s.chapter_id=self.chapter.currentData(); s.synopsis=self.synopsis.toPlainText().strip(); s.location=self.location.text().strip(); s.status=editable_combo_value(self.status, default='idee'); s.character_ids=[cb.property('characterId') for cb in self.character_checks if cb.isChecked()]; s.goal=self.goal.toPlainText().strip(); s.conflict=self.conflict.toPlainText().strip(); s.outcome=self.outcome.toPlainText().strip(); s.notes=self.notes.toPlainText().strip(); return s


SCENE_MIME = 'application/x-quietwriter-scene'


class SceneCard(QFrame):
    """Eén scène in de Outline. Slepen verplaatst hem (ook naar een ander hoofdstuk)."""

    def __init__(self, scene, character_names, edit_fn, delete_fn, move_fn=None, *, can_up=False, can_down=False,
                 number=None, move_targets=(), move_to_fn=None):
        super().__init__(); self.setObjectName('sceneCard')
        self.scene_id = scene.id
        self._press_pos = None
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip(tr('planning.outline.drag_tip', 'Sleep om de scène te verplaatsen, ook naar een ander hoofdstuk.'))
        lay=QVBoxLayout(self); lay.setContentsMargins(14,11,14,11); lay.setSpacing(5)
        top=QHBoxLayout(); top.setSpacing(4)
        title=QLabel(f'{number}. {scene.title}' if number else scene.title); title.setObjectName('sectionTitle'); title.setWordWrap(True)
        top.addWidget(title, 1)
        if move_fn is not None:
            up=QPushButton('↑'); up.setObjectName('compactButton'); up.setToolTip(tr('planning.outline.move_up', 'Scène omhoog')); up.setAccessibleName(up.toolTip()); up.setEnabled(can_up); up.clicked.connect(lambda:move_fn(scene.id,-1))
            down=QPushButton('↓'); down.setObjectName('compactButton'); down.setToolTip(tr('planning.outline.move_down', 'Scène omlaag')); down.setAccessibleName(down.toolTip()); down.setEnabled(can_down); down.clicked.connect(lambda:move_fn(scene.id,1))
            for button in (up, down):
                button.setCursor(Qt.ArrowCursor); top.addWidget(button)
        if move_to_fn is not None and move_targets:
            move_to = QToolButton(); move_to.setObjectName('compactButton'); move_to.setCursor(Qt.ArrowCursor)
            move_to.setText(tr('planning.outline.move_to', 'Verplaatsen naar') + ' ▾')
            move_to.setPopupMode(QToolButton.InstantPopup)
            menu = QMenu(move_to)
            for target_id, target_title in move_targets:
                action = menu.addAction(target_title)
                action.triggered.connect(lambda _=False, cid=target_id: move_to_fn(scene.id, cid))
            move_to.setMenu(menu)
            top.addWidget(move_to)
        edit=QPushButton(tr('planning.outline.edit', 'Bewerken')); edit.setObjectName('compactButton'); edit.setCursor(Qt.ArrowCursor)
        delete=QPushButton('×'); delete.setObjectName('compactButton'); delete.setCursor(Qt.ArrowCursor); delete.setToolTip(tr('planning.outline.delete_tip', 'Scène verwijderen')); delete.setAccessibleName(delete.toolTip())
        edit.clicked.connect(lambda:edit_fn(scene.id)); delete.clicked.connect(lambda:delete_fn(scene.id))
        top.addWidget(edit); top.addWidget(delete); lay.addLayout(top)
        if scene.synopsis: syn=QLabel(scene.synopsis); syn.setWordWrap(True); lay.addWidget(syn)
        status_display = {
            'idee': tr('planning.status.idea', 'Idee'),
            'uitgewerkt': tr('planning.status.developed', 'Uitgewerkt'),
            'geschreven': tr('planning.status.written', 'Geschreven'),
        }.get(scene.status, scene.status or tr('planning.status.idea', 'Idee'))
        status_prefix = '✓ ' if scene.status == 'geschreven' else ('◐ ' if scene.status == 'uitgewerkt' else '○ ')
        badge = QLabel(status_prefix + status_display); badge.setObjectName('sceneStatusBadge'); lay.addWidget(badge, 0, Qt.AlignLeft)
        meta=[]
        names=[character_names.get(cid) for cid in scene.character_ids if character_names.get(cid)]
        if names: meta.append(tr('planning.outline.meta.characters', 'personages: {names}', names=', '.join(names)))
        if scene.location: meta.append(tr('planning.outline.meta.location', 'locatie: {location}', location=scene.location))
        if meta: m=QLabel(' · '.join(meta)); m.setObjectName('muted'); m.setWordWrap(True); lay.addWidget(m)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is None or not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)
        if (event.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return super().mouseMoveEvent(event)
        self._press_pos = None
        mime = QMimeData(); mime.setData(SCENE_MIME, self.scene_id.encode('utf-8'))
        drag = QDrag(self); drag.setMimeData(mime)
        pixmap = self.grab()
        faded = pixmap.copy(); faded.fill(Qt.transparent)
        painter = QPainter(faded); painter.setOpacity(0.75); painter.drawPixmap(0, 0, pixmap); painter.end()
        drag.setPixmap(faded); drag.setHotSpot(event.position().toPoint())
        drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        self._press_pos = None
        super().mouseReleaseEvent(event)


class SceneGroup(QFrame):
    """Hoofdstukgroep in de Outline: neemt gesleepte scènes aan en toont waar ze komen."""

    def __init__(self, chapter_id, drop_fn, accepts_drops=True):
        super().__init__(); self.setObjectName('outlineChapterGroup')
        self.chapter_id = chapter_id
        self.drop_fn = drop_fn
        self._indicator_y = None
        self.setAcceptDrops(accepts_drops)

    def _cards(self):
        return [w for w in self.findChildren(SceneCard) if w.parent() is self and w.isVisible()]

    def drop_target(self, y: int):
        """(id van de scène waarvóór, y van de streep); None = achteraan."""
        cards = sorted(self._cards(), key=lambda card: card.geometry().top())
        for card in cards:
            geometry = card.geometry()
            if y < geometry.center().y():
                return card.scene_id, geometry.top() - 4
        if cards:
            return None, cards[-1].geometry().bottom() + 4
        return None, self.height() - 10

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SCENE_MIME):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasFormat(SCENE_MIME):
            event.ignore(); return
        _before, self._indicator_y = self.drop_target(int(event.position().y()))
        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._indicator_y = None; self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._indicator_y = None; self.update()
        if not event.mimeData().hasFormat(SCENE_MIME):
            event.ignore(); return
        scene_id = bytes(event.mimeData().data(SCENE_MIME)).decode('utf-8')
        before_id, _y = self.drop_target(int(event.position().y()))
        event.acceptProposedAction()
        # Na de drop wordt de Outline opnieuw opgebouwd; dat mag pas als de drag klaar is.
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self.drop_fn(scene_id, self.chapter_id, before_id))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._indicator_y is None:
            return
        painter = QPainter(self)
        color = self.palette().highlight().color()
        accent = self.property('accentColor')
        if accent:
            color = QColor(accent)
        painter.fillRect(12, int(self._indicator_y) - 1, self.width() - 24, 3, color)


class OutlinePage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.scenes=[]; self._collapsed_groups=set(); self._loaded_book_id=None
        root=QVBoxLayout(self); root.setContentsMargins(28,24,34,30); root.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.outline.title', 'Outline')); title.setObjectName('settingsPageTitle'); add=QPushButton(tr('planning.outline.new_scene', 'Nieuwe scène')); add.setObjectName('primaryButton'); add.clicked.connect(self.add_scene); self.toggle_all_button=QPushButton(); self.toggle_all_button.setObjectName('secondaryButton'); self.toggle_all_button.clicked.connect(self.toggle_all); top.addWidget(title); top.addStretch(); top.addWidget(self.toggle_all_button); top.addWidget(add); header=QWidget(); header.setMaximumWidth(1320); header_layout=QVBoxLayout(header); header_layout.setContentsMargins(0,0,0,0); header_layout.setSpacing(8); header_layout.addLayout(top)
        info=QLabel(tr('planning.outline.description_170', 'Bouw je verhaal op uit scènes en koppel ze aan hoofdstukken. De volgorde per hoofdstuk volgt je scènebreuken: scène 1 is de tekst vóór de eerste ***, scène 2 de tekst daarna. Gebruik de status om te zien wat nog een idee is, al is uitgewerkt of al is geschreven.')); info.setObjectName('muted'); info.setWordWrap(True); header_layout.addWidget(info); header_row=QHBoxLayout(); header_row.addWidget(header,1); header_row.addStretch(0); root.addLayout(header_row)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll_host=QWidget(); centered=QHBoxLayout(self.scroll_host); centered.setContentsMargins(0,0,0,0); centered.setSpacing(0)
        self.host=QWidget(); self.host.setMaximumWidth(1320); self.host.setMinimumWidth(0)
        self.list=QVBoxLayout(self.host); self.list.setContentsMargins(0,0,8,20); self.list.setSpacing(8)
        centered.addWidget(self.host,1); centered.addStretch(0)
        self.scroll.setWidget(self.scroll_host); root.addWidget(self.scroll,1)

    def load(self):
        book_id = getattr(self.owner.book, 'id', None)
        if book_id != self._loaded_book_id:
            self._collapsed_groups.clear()
            self._loaded_book_id = book_id
            # Ingeklapte groepen onthouden per boek (weergave, niet in het boek; 1.7).
            self._collapsed_groups.update(self._stored_collapsed(book_id))
        try:
            self.scenes = self.owner.store.load_scenes(self.owner.book) if self.owner.book else []
        except (CorruptSourceError, FuturePlanningFormatError) as exc:
            self.scenes = []
            self.owner.set_source_error('scenes', exc)
            self.setEnabled(False)
            self.refresh()
            return
        self.owner.clear_source_error('scenes')
        self.setEnabled(True)
        self.refresh()
    def _chapters(self): return [c for s in self.owner.book.sections for c in s.chapters] if self.owner.book else []
    def refresh(self):
        while self.list.count():
            item=self.list.takeAt(0)
            if item.widget(): item.widget().hide(); item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub=item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()
        chars=self.owner.characters_page.characters; names={c.id:c.name for c in chars}
        chapters=self._chapters(); valid_ids={c.id for c in chapters}
        groups=[(c.id,c.title,[s for s in self.scenes if s.chapter_id==c.id]) for c in chapters]
        groups.append((None,tr('planning.outline.loose_ideas', 'Losse ideeën'),[s for s in self.scenes if s.chapter_id is None]))
        orphaned=[s for s in self.scenes if s.chapter_id is not None and s.chapter_id not in valid_ids]
        if orphaned:
            groups.append(('__orphaned__',tr('planning.outline.orphaned', 'Verweesde scènes'),orphaned))
        targets=[(c.id, c.title) for c in chapters] + [(None, tr('planning.outline.loose_ideas', 'Losse ideeën'))]
        accent=self._accent()
        for cid,title,rows in groups:
            group_key = str(cid) if cid is not None else '__loose__'
            collapsed = group_key in self._collapsed_groups
            heading = QPushButton(('▸  ' if collapsed else '▾  ') + f'{title}  ·  {len(rows)}')
            heading.setObjectName('outlineChapterTitle')
            heading.setFlat(True)
            heading.setCursor(Qt.PointingHandCursor)
            heading.setToolTip(tr('planning.outline.toggle_group', 'Hoofdstukgroep in- of uitklappen'))
            heading.clicked.connect(lambda _=False, key=group_key: self.toggle_group(key))
            frame=SceneGroup(cid, self.drop_scene, accepts_drops=(cid != '__orphaned__'))
            frame.setProperty('accentColor', accent)
            group_layout=QVBoxLayout(frame)
            group_layout.setContentsMargins(10,6,10,10); group_layout.setSpacing(8)
            group_layout.addWidget(heading, 0, Qt.AlignLeft)
            if not collapsed:
                if not rows:
                    empty=QLabel(tr('planning.outline.empty_drop', 'Nog geen scènes. Sleep er een hierheen of kies Nieuwe scène.'))
                    empty.setObjectName('muted'); group_layout.addWidget(empty)
                numbered = cid in valid_ids
                for index, scene in enumerate(rows):
                    group_layout.addWidget(SceneCard(scene,names,self.edit_scene,self.delete_scene,self.move_scene,
                                                     can_up=index>0,can_down=index<len(rows)-1,
                                                     number=(index + 1) if numbered else None,
                                                     move_targets=[t for t in targets if t[0] != scene.chapter_id],
                                                     move_to_fn=self.move_scene_to))
                if numbered:
                    self._add_unplanned_row(group_layout, cid, rows)
            self.list.addWidget(frame)
        self._update_toggle_all(groups)
        self.list.addStretch()

    def _chapter_source(self, chapter_id):
        book = self.owner.book
        chapter = next((c for c in self._chapters() if c.id == chapter_id), None)
        if book is None or chapter is None:
            return ''
        try:
            return self.owner.store.library.read_chapter(book, chapter)
        except Exception:
            return ''

    def _add_unplanned_row(self, group_layout, chapter_id, rows):
        """Omgekeerd plannen: stukken tekst na de laatste geplande scène."""
        mapping = map_scenes(rows, self._chapter_source(chapter_id))
        if not mapping.unplanned:
            return
        line = QHBoxLayout()
        excerpts = '; '.join(f'{seg.index + 1}. {seg.excerpt or "…"}' for seg in mapping.unplanned[:3])
        if len(mapping.unplanned) > 3:
            excerpts += ' …'
        label = QLabel(tr('planning.outline.unplanned', 'In de tekst, nog niet in Planning: {excerpts}', excerpts=excerpts))
        label.setObjectName('muted'); label.setWordWrap(True)
        button = QPushButton(tr('chapter_context.add_unplanned', 'Toevoegen aan Planning'))
        button.setObjectName('compactButton')
        button.setToolTip(tr('chapter_context.add_unplanned_tip', 'Maakt voor deze stukken tekst een planningscène aan, met status Geschreven. Je tekst verandert niet.'))
        button.clicked.connect(lambda _=False, cid=chapter_id: self.add_unplanned(cid))
        line.addWidget(label, 1); line.addWidget(button, 0, Qt.AlignTop)
        group_layout.addLayout(line)

    def add_unplanned(self, chapter_id):
        # Altijd via de gedeelde actie: die leest Planning vers van schijf.
        self.owner.add_unplanned_scenes(chapter_id, self._chapter_source(chapter_id))

    def toggle_group(self, key):
        if key in self._collapsed_groups:
            self._collapsed_groups.remove(key)
        else:
            self._collapsed_groups.add(key)
        self._store_collapsed()
        self.refresh()

    def _group_keys(self):
        keys = [str(c.id) for c in self._chapters()] + ['__loose__']
        valid = {c.id for c in self._chapters()}
        if any(s.chapter_id is not None and s.chapter_id not in valid for s in self.scenes):
            keys.append('__orphaned__')
        return keys

    def toggle_all(self):
        keys = self._group_keys()
        if all(key in self._collapsed_groups for key in keys):
            self._collapsed_groups.difference_update(keys)
        else:
            self._collapsed_groups.update(keys)
        self._store_collapsed()
        self.refresh()

    def _update_toggle_all(self, groups):
        keys = [str(cid) if cid is not None else '__loose__' for cid, _t, _r in groups]
        everything_collapsed = bool(keys) and all(key in self._collapsed_groups for key in keys)
        self.toggle_all_button.setText(
            tr('planning.outline.expand_all', 'Alles uitklappen') if everything_collapsed
            else tr('planning.outline.collapse_all', 'Alles inklappen'))

    def _settings(self):
        main = getattr(self.owner, 'main', None)
        return getattr(main, 'settings', None)

    def _accent(self):
        try:
            from ...themes import THEMES
            settings = self._settings()
            theme = str(settings.value('theme', 'Helder')) if settings is not None else 'Helder'
            return THEMES.get(theme, THEMES['Helder'])['accent']
        except Exception:
            return ''

    def _collapsed_key(self, book_id):
        return f'planning/outline_collapsed/{book_id}'

    def _stored_collapsed(self, book_id):
        settings = self._settings()
        if settings is None or not book_id:
            return set()
        try:
            value = json.loads(str(settings.value(self._collapsed_key(book_id), '[]') or '[]'))
        except (TypeError, ValueError):
            return set()
        return {str(item) for item in value} if isinstance(value, list) else set()

    def _store_collapsed(self):
        settings = self._settings()
        if settings is None or not self._loaded_book_id:
            return
        settings.setValue(self._collapsed_key(self._loaded_book_id), json.dumps(sorted(self._collapsed_groups)))

    def move_scene_to(self, scene_id, chapter_id):
        """Naar het eind van een ander hoofdstuk (of Losse ideeën); alternatief voor slepen."""
        self.drop_scene(scene_id, chapter_id, None)

    def drop_scene(self, scene_id, chapter_id, before_id=None):
        """Zet een scène vóór ``before_id`` in ``chapter_id`` (None = achteraan). Alleen Planning verandert."""
        if chapter_id == '__orphaned__' or before_id == scene_id:
            return
        current = next((i for i, scene in enumerate(self.scenes) if scene.id == scene_id), None)
        if current is None:
            return
        before = copy.deepcopy(self.scenes)
        moved = self.scenes.pop(current)
        moved.chapter_id = chapter_id
        if before_id is not None:
            index = next((i for i, scene in enumerate(self.scenes) if scene.id == before_id), None)
            if index is None or self.scenes[index].chapter_id != chapter_id:
                self.scenes = before; return
        else:
            positions = [i for i, scene in enumerate(self.scenes) if scene.chapter_id == chapter_id]
            index = positions[-1] + 1 if positions else len(self.scenes)
        self.scenes.insert(index, moved)
        if [(s.id, s.chapter_id) for s in self.scenes] == [(s.id, s.chapter_id) for s in before]:
            self.scenes = before
            return
        key = str(chapter_id) if chapter_id is not None else '__loose__'
        if key in self._collapsed_groups:
            # Laat zien waar de scène heen ging.
            self._collapsed_groups.discard(key); self._store_collapsed()
        result = self._save()
        if result == 'failed':
            self.scenes = before
            self.refresh()

    def move_scene(self, scene_id, direction):
        """Change the order of scenes within their chapter; never mutate the manuscript."""
        current = next((i for i, scene in enumerate(self.scenes) if scene.id == scene_id), None)
        if current is None or direction not in (-1, 1):
            return
        chapter_id = self.scenes[current].chapter_id
        group_positions = [i for i, scene in enumerate(self.scenes) if scene.chapter_id == chapter_id]
        at = group_positions.index(current)
        destination = at + direction
        if not 0 <= destination < len(group_positions):
            return
        other = group_positions[destination]
        before = copy.deepcopy(self.scenes)
        self.scenes[current], self.scenes[other] = self.scenes[other], self.scenes[current]
        result = self._save()
        if result == 'failed':
            self.scenes = before
            self.refresh()

    def add_scene(self):
        scene=Scene(); dlg=SceneDialog(self,scene,self._chapters(),self.owner.characters_page.characters)
        if dlg.exec():
            before=copy.deepcopy(self.scenes)
            self.scenes.append(dlg.apply())
            result=self._save()
            if result == 'failed': self.scenes=before
    def edit_scene(self,sid):
        scene=next((s for s in self.scenes if s.id==sid),None)
        if not scene:return
        before=copy.deepcopy(self.scenes)
        dlg=SceneDialog(self,scene,self._chapters(),self.owner.characters_page.characters)
        if dlg.exec():
            dlg.apply()
            result=self._save()
            if result == 'failed': self.scenes=before
    def delete_scene(self,sid):
        if not confirm(
            self,
            tr('planning.outline.delete_title', 'Scène verwijderen'),
            tr('planning.outline.delete_confirm', 'Deze scène uit de outline verwijderen?'),
        ):
            return
        old=copy.deepcopy(self.scenes); self.scenes=[s for s in self.scenes if s.id!=sid]
        result=self._save()
        if result == 'failed': self.scenes=old
    def _save(self):
        result = self.owner.persist_scenes(self.scenes)
        if result == 'mine':
            self.refresh()
        return result
