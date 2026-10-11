from __future__ import annotations

import copy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
)

from ...planning_models import Scene
from ...storage import CorruptSourceError
from ...planning_validation import FuturePlanningFormatError
from ...i18n import tr
from ..dialogs import confirm
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
        root=QVBoxLayout(self); root.setSpacing(10); self.form_scroll=QScrollArea(); self.form_scroll.setWidgetResizable(True); self.form_scroll.setFrameShape(QFrame.NoFrame); form_host=QWidget(); form=QFormLayout(form_host); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
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
        form.addRow(tr('planning.outline.field.title', 'Titel'),self.title); form.addRow(tr('planning.outline.field.chapter', 'Hoofdstuk'),self.chapter); form.addRow(tr('planning.outline.field.synopsis', 'Synopsis'),self.synopsis); form.addRow(tr('planning.outline.field.location', 'Locatie'),self.location); form.addRow(tr('planning.outline.field.status', 'Status'),self.status)
        self.character_checks=[]; chars=QWidget(); cl=QVBoxLayout(chars); cl.setContentsMargins(0,0,0,0)
        for char in characters:
            cb=QCheckBox(char.name); cb.setProperty('characterId',char.id); cb.setChecked(char.id in scene.character_ids); cl.addWidget(cb); self.character_checks.append(cb)
        form.addRow(tr('planning.outline.field.characters', 'Personages'),chars)
        self.goal=self._text(scene.goal); self.conflict=self._text(scene.conflict); self.outcome=self._text(scene.outcome); self.notes=self._text(scene.notes)
        # All fields stay visible; understated headings explain the grouping.
        form.addRow(self._section_heading(tr('planning.outline.section.depth', 'Verdieping')))
        form.addRow(tr('planning.outline.field.goal', 'Doel'), self.goal)
        form.addRow(tr('planning.outline.field.conflict', 'Conflict'), self.conflict)
        form.addRow(tr('planning.outline.field.outcome', 'Uitkomst'), self.outcome)
        form.addRow(tr('planning.outline.field.notes', 'Notities'), self.notes)
        self.form_scroll.setWidget(form_host); root.addWidget(self.form_scroll,1); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); save_button=buttons.button(QDialogButtonBox.Save); cancel_button=buttons.button(QDialogButtonBox.Cancel); save_button.setText(tr('common.save', 'Opslaan')); cancel_button.setText(tr('common.cancel', 'Annuleren')); save_button.setObjectName('primaryButton'); cancel_button.setObjectName('secondaryButton'); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    @staticmethod
    def _section_heading(text):
        label=QLabel(text); label.setObjectName('sectionTitle'); return label
    def _text(self,value):
        e=QTextEdit(); e.setPlainText(value); e.setFixedHeight(108); return e
    def apply(self):
        s=self.scene; s.title=self.title.text().strip() or tr('planning.outline.untitled_scene', 'Naamloze scène'); s.chapter_id=self.chapter.currentData(); s.synopsis=self.synopsis.toPlainText().strip(); s.location=self.location.text().strip(); s.status=editable_combo_value(self.status, default='idee'); s.character_ids=[cb.property('characterId') for cb in self.character_checks if cb.isChecked()]; s.goal=self.goal.toPlainText().strip(); s.conflict=self.conflict.toPlainText().strip(); s.outcome=self.outcome.toPlainText().strip(); s.notes=self.notes.toPlainText().strip(); return s


class SceneCard(QFrame):
    def __init__(self, scene, character_names, edit_fn, delete_fn, move_fn=None, *, can_up=False, can_down=False):
        super().__init__(); self.setObjectName('sceneCard')
        lay=QVBoxLayout(self); lay.setContentsMargins(14,11,14,11); lay.setSpacing(5)
        top=QHBoxLayout(); title=QLabel(scene.title); title.setObjectName('sectionTitle'); edit=QPushButton(tr('planning.outline.edit', 'Bewerken')); edit.setObjectName('compactButton'); delete=QPushButton('×'); delete.setObjectName('compactButton'); delete.setToolTip(tr('planning.outline.delete_tip', 'Scène verwijderen')); edit.clicked.connect(lambda:edit_fn(scene.id)); delete.clicked.connect(lambda:delete_fn(scene.id)); top.addWidget(title); top.addStretch()
        if move_fn is not None:
            up=QPushButton(tr('planning.outline.move_up', 'Scène omhoog')); up.setObjectName('compactButton'); up.setToolTip(tr('planning.outline.move_up', 'Scène omhoog')); up.setEnabled(can_up); up.clicked.connect(lambda:move_fn(scene.id,-1))
            down=QPushButton(tr('planning.outline.move_down', 'Scène omlaag')); down.setObjectName('compactButton'); down.setToolTip(tr('planning.outline.move_down', 'Scène omlaag')); down.setEnabled(can_down); down.clicked.connect(lambda:move_fn(scene.id,1))
            top.addWidget(up); top.addWidget(down)
        top.addWidget(edit); top.addWidget(delete); lay.addLayout(top)
        if scene.synopsis: syn=QLabel(scene.synopsis); syn.setWordWrap(True); lay.addWidget(syn)
        status_display = {
            'idee': tr('planning.status.idea', 'Idee'),
            'uitgewerkt': tr('planning.status.developed', 'Uitgewerkt'),
            'geschreven': tr('planning.status.written', 'Geschreven'),
        }.get(scene.status, scene.status or tr('planning.status.idea', 'Idee'))
        status_prefix = '✓ ' if scene.status == 'geschreven' else ('◐ ' if scene.status == 'uitgewerkt' else '○ ')
        badge = QLabel(status_prefix + status_display); badge.setObjectName('sceneStatusBadge'); lay.addWidget(badge, 0)
        meta=[]
        names=[character_names.get(cid) for cid in scene.character_ids if character_names.get(cid)]
        if names: meta.append(tr('planning.outline.meta.characters', 'personages: {names}', names=', '.join(names)))
        if scene.location: meta.append(tr('planning.outline.meta.location', 'locatie: {location}', location=scene.location))
        if meta: m=QLabel(' · '.join(meta)); m.setObjectName('muted'); m.setWordWrap(True); lay.addWidget(m)


class OutlinePage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.scenes=[]; self._collapsed_groups=set(); self._loaded_book_id=None
        root=QVBoxLayout(self); root.setContentsMargins(28,24,34,30); root.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.outline.title', 'Outline')); title.setObjectName('title'); add=QPushButton(tr('planning.outline.new_scene', 'Nieuwe scène')); add.setObjectName('primaryButton'); add.clicked.connect(self.add_scene); top.addWidget(title); top.addStretch(); top.addWidget(add); header=QWidget(); header.setMaximumWidth(1320); header_layout=QVBoxLayout(header); header_layout.setContentsMargins(0,0,0,0); header_layout.setSpacing(8); header_layout.addLayout(top)
        info=QLabel(tr('planning.outline.description', 'Bouw je verhaal op uit scènes en koppel ze aan hoofdstukken. Leg per scène vast wat er moet gebeuren en gebruik de status om te zien wat nog een idee is, al is uitgewerkt of al is geschreven. Open scènes kunnen in een leeg hoofdstuk als planninghulp verschijnen.')); info.setObjectName('muted'); info.setWordWrap(True); header_layout.addWidget(info); header_row=QHBoxLayout(); header_row.addWidget(header,1); header_row.addStretch(0); root.addLayout(header_row)
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
            if item.widget(): item.widget().deleteLater()
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
        for cid,title,rows in groups:
            group_key = str(cid) if cid is not None else '__loose__'
            collapsed = group_key in self._collapsed_groups
            heading = QPushButton(('▸ ' if collapsed else '▾ ') + f'{title} ({len(rows)})')
            heading.setObjectName('outlineChapterTitle')
            heading.setFlat(True)
            heading.setToolTip(tr('planning.outline.toggle_group', 'Hoofdstukgroep in- of uitklappen'))
            heading.clicked.connect(lambda _=False, key=group_key: self.toggle_group(key))
            frame=QFrame(); frame.setObjectName('outlineChapterGroup')
            group_layout=QVBoxLayout(frame)
            group_layout.setContentsMargins(8,8,8,10); group_layout.setSpacing(8)
            group_layout.addWidget(heading)
            if not collapsed:
                if not rows:
                    empty=QLabel(tr('planning.outline.empty', 'Nog geen scènes'))
                    empty.setObjectName('muted'); group_layout.addWidget(empty)
                for index, scene in enumerate(rows):
                    group_layout.addWidget(SceneCard(scene,names,self.edit_scene,self.delete_scene,self.move_scene,
                                                     can_up=index>0,can_down=index<len(rows)-1))
            self.list.addWidget(frame)
        self.list.addStretch()

    def toggle_group(self, key):
        if key in self._collapsed_groups:
            self._collapsed_groups.remove(key)
        else:
            self._collapsed_groups.add(key)
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
