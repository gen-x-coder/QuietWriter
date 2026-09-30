from __future__ import annotations

import copy

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
)

from ...planning_models import Scene
from ...storage import CorruptSourceError
from ...planning_validation import FuturePlanningFormatError
from ...i18n import tr
from ..dialogs import confirm


class SceneDialog(QDialog):
    def __init__(self, parent, scene: Scene, chapters, characters):
        super().__init__(parent); self.scene=scene; self.setWindowTitle(tr('planning.outline.scene_title', 'Scène')); self.resize(610,700)
        root=QVBoxLayout(self); form=QFormLayout(); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.title=QLineEdit(scene.title); self.synopsis=QTextEdit(); self.synopsis.setPlainText(scene.synopsis); self.synopsis.setFixedHeight(90)
        self.chapter=QComboBox(); self.chapter.addItem(tr('planning.outline.loose_idea', 'Los idee'), None)
        for ch in chapters: self.chapter.addItem(ch.title, ch.id)
        idx=self.chapter.findData(scene.chapter_id); self.chapter.setCurrentIndex(max(0,idx))
        self.location=QLineEdit(scene.location); self.status=QComboBox(); self.status.setEditable(True); self.status.addItems(['idee','uitgewerkt','geschreven']); self.status.setCurrentText(scene.status)
        form.addRow(tr('planning.outline.field.title', 'Titel'),self.title); form.addRow(tr('planning.outline.field.chapter', 'Hoofdstuk'),self.chapter); form.addRow(tr('planning.outline.field.synopsis', 'Synopsis'),self.synopsis); form.addRow(tr('planning.outline.field.location', 'Locatie'),self.location); form.addRow(tr('planning.outline.field.status', 'Status'),self.status)
        self.character_checks=[]; chars=QWidget(); cl=QVBoxLayout(chars); cl.setContentsMargins(0,0,0,0)
        for char in characters:
            cb=QCheckBox(char.name); cb.setProperty('characterId',char.id); cb.setChecked(char.id in scene.character_ids); cl.addWidget(cb); self.character_checks.append(cb)
        form.addRow(tr('planning.outline.field.characters', 'Personages'),chars)
        self.goal=self._text(scene.goal); self.conflict=self._text(scene.conflict); self.outcome=self._text(scene.outcome); self.notes=self._text(scene.notes)
        form.addRow(tr('planning.outline.field.goal', 'Doel'),self.goal); form.addRow(tr('planning.outline.field.conflict', 'Conflict'),self.conflict); form.addRow(tr('planning.outline.field.outcome', 'Uitkomst'),self.outcome); form.addRow(tr('planning.outline.field.notes', 'Notities'),self.notes)
        root.addLayout(form); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); save_button=buttons.button(QDialogButtonBox.Save); cancel_button=buttons.button(QDialogButtonBox.Cancel); save_button.setText(tr('common.save', 'Opslaan')); cancel_button.setText(tr('common.cancel', 'Annuleren')); save_button.setObjectName('primaryButton'); cancel_button.setObjectName('secondaryButton'); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _text(self,value):
        e=QTextEdit(); e.setPlainText(value); e.setFixedHeight(74); return e
    def apply(self):
        s=self.scene; s.title=self.title.text().strip() or tr('planning.outline.untitled_scene', 'Naamloze scène'); s.chapter_id=self.chapter.currentData(); s.synopsis=self.synopsis.toPlainText().strip(); s.location=self.location.text().strip(); s.status=self.status.currentText().strip() or 'idee'; s.character_ids=[cb.property('characterId') for cb in self.character_checks if cb.isChecked()]; s.goal=self.goal.toPlainText().strip(); s.conflict=self.conflict.toPlainText().strip(); s.outcome=self.outcome.toPlainText().strip(); s.notes=self.notes.toPlainText().strip(); return s


class SceneCard(QFrame):
    def __init__(self, scene, character_names, edit_fn, delete_fn):
        super().__init__(); self.setObjectName('sceneCard')
        lay=QVBoxLayout(self); lay.setContentsMargins(14,11,14,11); lay.setSpacing(5)
        top=QHBoxLayout(); title=QLabel(scene.title); title.setObjectName('sectionTitle'); edit=QPushButton(tr('planning.outline.edit', 'Bewerken')); edit.setObjectName('compactButton'); delete=QPushButton('×'); delete.setObjectName('compactButton'); delete.setToolTip(tr('planning.outline.delete_tip', 'Scène verwijderen')); edit.clicked.connect(lambda:edit_fn(scene.id)); delete.clicked.connect(lambda:delete_fn(scene.id)); top.addWidget(title); top.addStretch(); top.addWidget(edit); top.addWidget(delete); lay.addLayout(top)
        if scene.synopsis: syn=QLabel(scene.synopsis); syn.setWordWrap(True); lay.addWidget(syn)
        meta=[]
        names=[character_names.get(cid) for cid in scene.character_ids if character_names.get(cid)]
        if names: meta.append(tr('planning.outline.meta.characters', 'personages: {names}', names=', '.join(names)))
        if scene.location: meta.append(tr('planning.outline.meta.location', 'locatie: {location}', location=scene.location))
        if scene.status: meta.append(tr('planning.outline.meta.status', 'status: {status}', status=scene.status))
        if meta: m=QLabel(' · '.join(meta)); m.setObjectName('muted'); m.setWordWrap(True); lay.addWidget(m)


class OutlinePage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.scenes=[]
        root=QVBoxLayout(self); root.setContentsMargins(28,24,34,30); root.setSpacing(12)
        top=QHBoxLayout(); title=QLabel(tr('planning.outline.title', 'Outline')); title.setObjectName('title'); add=QPushButton(tr('planning.outline.new_scene', 'Nieuwe scène')); add.setObjectName('primaryButton'); add.clicked.connect(self.add_scene); top.addWidget(title); top.addStretch(); top.addWidget(add); root.addLayout(top)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); self.host=QWidget(); self.list=QVBoxLayout(self.host); self.list.setContentsMargins(0,0,8,20); self.list.setSpacing(8); self.scroll.setWidget(self.host); root.addWidget(self.scroll,1)

    def load(self):
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
        for _cid,title,rows in groups:
            heading=QLabel(title); heading.setObjectName('outlineChapterTitle'); self.list.addWidget(heading)
            if not rows:
                empty=QLabel(tr('planning.outline.empty', 'Nog geen scènes')); empty.setObjectName('muted'); self.list.addWidget(empty)
            for scene in rows: self.list.addWidget(SceneCard(scene,names,self.edit_scene,self.delete_scene))
            self.list.addSpacing(8)
        self.list.addStretch()

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
