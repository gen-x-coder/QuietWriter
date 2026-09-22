from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
)

from ...planning_models import Scene


class SceneDialog(QDialog):
    def __init__(self, parent, scene: Scene, chapters, characters):
        super().__init__(parent); self.scene=scene; self.setWindowTitle('Scène'); self.resize(610,700)
        root=QVBoxLayout(self); form=QFormLayout(); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.title=QLineEdit(scene.title); self.synopsis=QTextEdit(); self.synopsis.setPlainText(scene.synopsis); self.synopsis.setFixedHeight(90)
        self.chapter=QComboBox(); self.chapter.addItem('Los idee', None)
        for ch in chapters: self.chapter.addItem(ch.title, ch.id)
        idx=self.chapter.findData(scene.chapter_id); self.chapter.setCurrentIndex(max(0,idx))
        self.location=QLineEdit(scene.location); self.status=QComboBox(); self.status.setEditable(True); self.status.addItems(['idee','uitgewerkt','geschreven']); self.status.setCurrentText(scene.status)
        form.addRow('Titel',self.title); form.addRow('Hoofdstuk',self.chapter); form.addRow('Synopsis',self.synopsis); form.addRow('Locatie',self.location); form.addRow('Status',self.status)
        self.character_checks=[]; chars=QWidget(); cl=QVBoxLayout(chars); cl.setContentsMargins(0,0,0,0)
        for char in characters:
            cb=QCheckBox(char.name); cb.setProperty('characterId',char.id); cb.setChecked(char.id in scene.character_ids); cl.addWidget(cb); self.character_checks.append(cb)
        form.addRow('Personages',chars)
        self.goal=self._text(scene.goal); self.conflict=self._text(scene.conflict); self.outcome=self._text(scene.outcome); self.notes=self._text(scene.notes)
        form.addRow('Doel',self.goal); form.addRow('Conflict',self.conflict); form.addRow('Uitkomst',self.outcome); form.addRow('Notities',self.notes)
        root.addLayout(form); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)
    def _text(self,value):
        e=QTextEdit(); e.setPlainText(value); e.setFixedHeight(74); return e
    def apply(self):
        s=self.scene; s.title=self.title.text().strip() or 'Naamloze scène'; s.chapter_id=self.chapter.currentData(); s.synopsis=self.synopsis.toPlainText().strip(); s.location=self.location.text().strip(); s.status=self.status.currentText().strip() or 'idee'; s.character_ids=[cb.property('characterId') for cb in self.character_checks if cb.isChecked()]; s.goal=self.goal.toPlainText().strip(); s.conflict=self.conflict.toPlainText().strip(); s.outcome=self.outcome.toPlainText().strip(); s.notes=self.notes.toPlainText().strip(); return s


class SceneCard(QFrame):
    def __init__(self, scene, character_names, edit_fn, delete_fn):
        super().__init__(); self.setObjectName('sceneCard')
        lay=QVBoxLayout(self); lay.setContentsMargins(14,11,14,11); lay.setSpacing(5)
        top=QHBoxLayout(); title=QLabel(scene.title); title.setObjectName('sectionTitle'); edit=QPushButton('Bewerken'); edit.setObjectName('compactButton'); delete=QPushButton('×'); delete.setObjectName('compactButton'); delete.setToolTip('Scène verwijderen'); edit.clicked.connect(lambda:edit_fn(scene.id)); delete.clicked.connect(lambda:delete_fn(scene.id)); top.addWidget(title); top.addStretch(); top.addWidget(edit); top.addWidget(delete); lay.addLayout(top)
        if scene.synopsis: syn=QLabel(scene.synopsis); syn.setWordWrap(True); lay.addWidget(syn)
        meta=[]
        names=[character_names.get(cid) for cid in scene.character_ids if character_names.get(cid)]
        if names: meta.append('personages: '+', '.join(names))
        if scene.location: meta.append('locatie: '+scene.location)
        if scene.status: meta.append('status: '+scene.status)
        if meta: m=QLabel(' · '.join(meta)); m.setObjectName('muted'); m.setWordWrap(True); lay.addWidget(m)


class OutlinePage(QWidget):
    def __init__(self, planning_page):
        super().__init__(); self.owner=planning_page; self.scenes=[]
        root=QVBoxLayout(self); root.setContentsMargins(28,24,34,30); root.setSpacing(12)
        top=QHBoxLayout(); title=QLabel('Outline'); title.setObjectName('title'); add=QPushButton('Nieuwe scène'); add.setObjectName('primaryButton'); add.clicked.connect(self.add_scene); top.addWidget(title); top.addStretch(); top.addWidget(add); root.addLayout(top)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); self.host=QWidget(); self.list=QVBoxLayout(self.host); self.list.setContentsMargins(0,0,8,20); self.list.setSpacing(8); self.scroll.setWidget(self.host); root.addWidget(self.scroll,1)

    def load(self): self.scenes=self.owner.store.load_scenes(self.owner.book) if self.owner.book else []; self.refresh()
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
        groups=[(c.id,c.title) for c in self._chapters()]+[(None,'Losse ideeën')]
        for cid,title in groups:
            heading=QLabel(title); heading.setObjectName('outlineChapterTitle'); self.list.addWidget(heading)
            rows=[s for s in self.scenes if s.chapter_id==cid]
            if not rows:
                empty=QLabel('Nog geen scènes'); empty.setObjectName('muted'); self.list.addWidget(empty)
            for scene in rows: self.list.addWidget(SceneCard(scene,names,self.edit_scene,self.delete_scene))
            self.list.addSpacing(8)
        self.list.addStretch()

    def add_scene(self):
        scene=Scene(); dlg=SceneDialog(self,scene,self._chapters(),self.owner.characters_page.characters)
        if dlg.exec(): self.scenes.append(dlg.apply()); self._save()
    def edit_scene(self,sid):
        scene=next((s for s in self.scenes if s.id==sid),None)
        if not scene:return
        dlg=SceneDialog(self,scene,self._chapters(),self.owner.characters_page.characters)
        if dlg.exec(): dlg.apply(); self._save()
    def delete_scene(self,sid):
        from PySide6.QtWidgets import QMessageBox
        if QMessageBox.question(self,'Scène verwijderen','Deze scène uit de outline verwijderen?') != QMessageBox.Yes:return
        old=list(self.scenes); self.scenes=[s for s in self.scenes if s.id!=sid]
        if not self._save(): self.scenes=old
    def _save(self):
        if self.owner.persist_scenes(self.scenes): self.refresh(); return True
        return False
