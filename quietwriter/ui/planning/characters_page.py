from __future__ import annotations

from PySide6.QtCore import Qt, Signal
import copy
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
)

from ..current_page_stack import CurrentPageStack
from ..dialogs import confirm
from ...planning_models import Character, Relation
from ...i18n import tr


RELATION_PAIRS = {
    'ouder van': 'kind van', 'kind van': 'ouder van',
    'vader van': 'kind van', 'moeder van': 'kind van',
    'zoon van': 'ouder van', 'dochter van': 'ouder van',
    'partner van': 'partner van', 'vriend van': 'vriend van',
    'collega van': 'collega van', 'mentor van': 'leerling van', 'leerling van': 'mentor van',
}


class CharacterDetail(QWidget):
    saveRequested = Signal(object)
    deleteRequested = Signal(str)
    relationRequested = Signal(str, str, str)
    relationDeleteRequested = Signal(str, str)
    navigateCharacter = Signal(str)

    def __init__(self):
        super().__init__()
        self.character: Character | None = None
        self.characters: list[Character] = []
        self.is_new = False
        outer = QVBoxLayout(self); outer.setContentsMargins(34, 26, 42, 34); outer.setSpacing(12)
        top = QHBoxLayout()
        self.title = QLabel(tr('planning.characters.character', 'Personage')); self.title.setObjectName('title')
        self.delete = QPushButton(tr('planning.characters.delete', 'Verwijderen')); self.delete.setObjectName('dangerButton'); self.delete.clicked.connect(self._delete)
        top.addWidget(self.title); top.addStretch(); top.addWidget(self.delete)
        outer.addLayout(top)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget(); self.form = QVBoxLayout(host); self.form.setContentsMargins(0, 0, 12, 20); self.form.setSpacing(12)
        self.name = self._line(tr('planning.characters.name', 'Naam'))
        self.role = self._line(tr('planning.characters.role', 'Rol in het verhaal'))
        self.description = self._text(tr('planning.characters.description', 'Korte beschrijving'), 72)
        self.form.addSpacing(8)
        details = QLabel(tr('planning.characters.character_section', 'Karakter')); details.setObjectName('sectionTitle'); self.form.addWidget(details)
        self.personality = self._text(tr('planning.characters.personality', 'Persoonlijkheid'))
        self.motivation = self._text(tr('planning.characters.motivation', 'Motivatie'))
        self.goals = self._text(tr('planning.characters.goals', 'Doelen'))
        self.fears = self._text(tr('planning.characters.fears', 'Angsten / zwakke plekken'))
        self.values = self._text(tr('planning.characters.values', 'Waarden / overtuigingen'))
        self.conflicts = self._text(tr('planning.characters.conflicts', 'Innerlijke / uiterlijke conflicten'))
        self.voice = self._text(tr('planning.characters.voice', 'Manier van spreken'))
        self.under_pressure = self._text(tr('planning.characters.under_pressure', 'Gedrag onder druk'))
        self.background = self._text(tr('planning.characters.background', 'Achtergrond'))
        self.notes = self._text(tr('planning.characters.notes', 'Notities'))

        self.form.addSpacing(8)
        rel_title = QLabel(tr('planning.characters.relations', 'Relaties')); rel_title.setObjectName('sectionTitle'); self.form.addWidget(rel_title)
        self.relations_box = QVBoxLayout(); self.relations_box.setSpacing(6); self.form.addLayout(self.relations_box)
        add = QHBoxLayout()
        self.rel_type = QComboBox(); self.rel_type.setEditable(True); self.rel_type.addItems(sorted(RELATION_PAIRS))
        self.rel_target = QComboBox()
        add_btn = QPushButton(tr('planning.characters.add_relation', 'Relatie toevoegen')); add_btn.clicked.connect(self._add_relation)
        add.addWidget(self.rel_type, 1); add.addWidget(self.rel_target, 1); add.addWidget(add_btn)
        self.form.addLayout(add)
        self.relation_controls = (self.rel_type, self.rel_target, add_btn)
        self.form.addStretch()
        scroll.setWidget(host); outer.addWidget(scroll, 1)
        save = QPushButton(tr('common.save', 'Opslaan')); save.setObjectName('primaryButton'); save.clicked.connect(self._save)
        outer.addWidget(save, 0, Qt.AlignRight)

    def _line(self, label):
        lab = QLabel(label); lab.setObjectName('settingsFieldLabel'); self.form.addWidget(lab)
        edit = QLineEdit(); self.form.addWidget(edit); return edit

    def _text(self, label, height=88):
        lab = QLabel(label); lab.setObjectName('settingsFieldLabel'); self.form.addWidget(lab)
        edit = QTextEdit(); edit.setAcceptRichText(False); edit.setFixedHeight(height); self.form.addWidget(edit); return edit

    def set_character(self, character: Character | None, characters: list[Character], *, is_new: bool = False):
        self.character = character; self.characters = characters; self.is_new = is_new
        if character is None:
            self.hide()
            return
        self.show()
        self.setEnabled(True)
        self.title.setText(tr('planning.characters.new', 'Nieuw personage') if is_new else (character.name or tr('planning.characters.character', 'Personage')))
        self.delete.setVisible(not is_new)
        for widget in self.relation_controls:
            widget.setEnabled(not is_new)
        for widget, value in (
            (self.name, character.name), (self.role, character.role),
        ): widget.setText(value)
        for widget, value in (
            (self.description, character.description), (self.personality, character.personality),
            (self.motivation, character.motivation), (self.goals, character.goals),
            (self.fears, character.fears), (self.values, character.values),
            (self.conflicts, character.conflicts), (self.background, character.background),
            (self.voice, character.voice), (self.under_pressure, character.under_pressure),
            (self.notes, character.notes),
        ): widget.setPlainText(value)
        self.rel_target.clear()
        for other in characters:
            if other.id != character.id:
                self.rel_target.addItem(other.name, other.id)
        self._render_relations()

    def _render_relations(self):
        while self.relations_box.count():
            item = self.relations_box.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not self.character or not self.character.relations:
            muted = QLabel(tr('planning.characters.no_relations', 'Nog geen relaties.')); muted.setObjectName('muted'); self.relations_box.addWidget(muted); return
        names = {c.id: c.name for c in self.characters}
        for relation in self.character.relations:
            holder = QWidget(); hl = QHBoxLayout(holder); hl.setContentsMargins(0,0,0,0); hl.setSpacing(4)
            unknown_label = tr('planning.characters.unknown', 'Onbekend personage')
            row = QPushButton(f'→  {relation.type}  {names.get(relation.target_id, unknown_label)}')
            row.setObjectName('relationChip'); row.setCursor(Qt.PointingHandCursor)
            row.clicked.connect(lambda _=False, cid=relation.target_id: self.navigateCharacter.emit(cid))
            remove = QPushButton('×'); remove.setObjectName('compactButton'); remove.setToolTip(tr('planning.characters.remove_relation', 'Relatie verwijderen'))
            remove.clicked.connect(lambda _=False, rid=relation.id: self.relationDeleteRequested.emit(self.character.id, rid))
            hl.addWidget(row); hl.addWidget(remove); hl.addStretch(); self.relations_box.addWidget(holder)

    def _collect(self):
        # Never mutate the stored Character before persistence succeeds. The
        # detail editor works on a candidate copy so a failed save cannot leak
        # into a later, unrelated successful planning write.
        if not self.character:
            return None
        c = copy.deepcopy(self.character)
        c.name = self.name.text().strip() or tr('planning.characters.untitled', 'Naamloos personage'); c.role = self.role.text().strip()
        c.description = self.description.toPlainText().strip(); c.personality = self.personality.toPlainText().strip()
        c.motivation = self.motivation.toPlainText().strip(); c.goals = self.goals.toPlainText().strip()
        c.fears = self.fears.toPlainText().strip(); c.values = self.values.toPlainText().strip()
        c.conflicts = self.conflicts.toPlainText().strip(); c.background = self.background.toPlainText().strip()
        c.voice = self.voice.toPlainText().strip(); c.under_pressure = self.under_pressure.toPlainText().strip()
        c.notes = self.notes.toPlainText().strip(); return c

    def _save(self):
        c = self._collect()
        if c: self.saveRequested.emit(c)

    def _delete(self):
        if self.character: self.deleteRequested.emit(self.character.id)

    def _add_relation(self):
        if not self.character or self.rel_target.currentIndex() < 0: return
        relation_type = self.rel_type.currentText().strip() or 'kent'
        self.relationRequested.emit(self.character.id, self.rel_target.currentData(), relation_type)


class CharactersPage(QWidget):
    changed = Signal()

    def __init__(self, planning_page):
        super().__init__(); self.owner = planning_page; self.characters: list[Character] = []; self._draft: Character | None = None
        root = QVBoxLayout(self); root.setContentsMargins(28,24,34,30); root.setSpacing(12)
        top = QHBoxLayout()
        page_title = QLabel(tr('planning.characters.title', 'Personages')); page_title.setObjectName('title')
        add = QPushButton(tr('planning.characters.new', 'Nieuw personage')); add.setObjectName('primaryButton'); add.clicked.connect(self.add_character)
        top.addWidget(page_title); top.addStretch(); top.addWidget(add)
        root.addLayout(top)

        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0)
        side = QFrame(); side.setObjectName('planningListPanel'); side.setFixedWidth(190)
        sl = QVBoxLayout(side); sl.setContentsMargins(16,18,14,22); sl.setSpacing(8)
        list_label=QLabel(tr('planning.characters.list_heading', 'PERSONAGES')); list_label.setObjectName('planningMicroLabel'); sl.addWidget(list_label)
        self.list = QListWidget(); self.list.currentItemChanged.connect(self._selection_changed); sl.addWidget(self.list,1)
        self.detail = CharacterDetail(); self.detail.saveRequested.connect(self.save_character); self.detail.deleteRequested.connect(self.delete_character); self.detail.relationRequested.connect(self.add_relation); self.detail.relationDeleteRequested.connect(self.delete_relation); self.detail.navigateCharacter.connect(self.select_character)
        self.canvas = CurrentPageStack(); self.canvas.setObjectName('planningCanvas')
        self.blank = QWidget(); self.blank.setObjectName('planningBlankCanvas')
        self.canvas.addWidget(self.blank); self.canvas.addWidget(self.detail)
        body.addWidget(side); body.addWidget(self.canvas,1)
        root.addLayout(body,1)
        self.canvas.setCurrentWidget(self.blank)

    def load(self):
        self._draft = None
        self.characters = self.owner.store.load_characters(self.owner.book) if self.owner.book else []
        self.refresh_list()
        self.close_detail()

    def refresh_list(self, keep_id=None):
        self.list.blockSignals(True); self.list.clear()
        selected = None
        for c in self.characters:
            item = QListWidgetItem(c.name + (f'\n{c.role}' if c.role else '')); item.setData(Qt.UserRole,c.id); self.list.addItem(item)
            if c.id == keep_id: selected = item
        self.list.blockSignals(False)
        if selected:
            self.list.setCurrentItem(selected)
        else:
            self.list.clearSelection(); self.list.setCurrentRow(-1)

    def close_detail(self):
        self._draft = None
        self.list.blockSignals(True)
        self.list.clearSelection(); self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.detail.set_character(None, self.characters)
        self.canvas.setCurrentWidget(self.blank)

    def _selection_changed(self, current, _previous=None):
        self._draft = None
        cid = current.data(Qt.UserRole) if current else None
        char = next((c for c in self.characters if c.id == cid), None)
        self.detail.set_character(char, self.characters)
        self.canvas.setCurrentWidget(self.detail if char else self.blank)

    def select_character(self, cid):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == cid:
                self.list.setCurrentRow(i); break

    def add_character(self):
        # Creating a personage starts as an in-memory draft. Nothing is written
        # until the user explicitly presses Opslaan.
        self.list.blockSignals(True)
        self.list.clearSelection(); self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self._draft = Character(name='')
        self.detail.set_character(self._draft, self.characters + [self._draft], is_new=True)
        self.canvas.setCurrentWidget(self.detail)
        self.detail.name.setFocus()

    def save_character(self, character):
        if self._draft is not None and character.id == self._draft.id:
            candidate = copy.deepcopy(self.characters) + [character]
        else:
            candidate = []
            found = False
            for current in self.characters:
                if current.id == character.id:
                    candidate.append(character); found = True
                else:
                    candidate.append(copy.deepcopy(current))
            if not found:
                return False
        result = self.owner.persist_characters(candidate)
        if result == 'failed':
            return False
        if result == 'disk':
            # The central live-book adoption already reloaded the disk version.
            return True
        self.characters = candidate
        self.refresh_list()
        self.close_detail()
        self.changed.emit()
        return True

    def _draft_has_content(self):
        if self._draft is None or not self.detail.is_new:
            return False
        fields = [self.detail.name, self.detail.role]
        texts = [widget.text().strip() for widget in fields]
        texts.extend(widget.toPlainText().strip() for widget in (
            self.detail.description, self.detail.personality, self.detail.motivation,
            self.detail.goals, self.detail.fears, self.detail.values,
            self.detail.conflicts, self.detail.background, self.detail.voice,
            self.detail.under_pressure, self.detail.notes,
        ))
        return any(texts)

    def pending_editor_snapshot(self):
        """Capture an unsaved *new-character* draft before same-book reload.

        Existing characters already have an authoritative stored counterpart; a
        future merge policy can treat field-level edits separately. The reviewed
        data-loss path concerns the in-memory new-character draft, which has no
        disk representation at all and therefore must be kept intact.
        """
        if self._draft is None or not self.detail.is_new or self.detail.character is None:
            return None
        candidate = self.detail._collect()
        return copy.deepcopy(candidate) if candidate is not None else None

    def restore_editor_snapshot(self, snapshot):
        if snapshot is None:
            return
        candidate = copy.deepcopy(snapshot)
        self.list.blockSignals(True)
        self.list.clearSelection(); self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self._draft = candidate
        self.detail.set_character(candidate, self.characters + [candidate], is_new=True)
        self.canvas.setCurrentWidget(self.detail)

    def save_pending(self):
        if self._draft is None or not self.detail.is_new:
            return True
        if not self._draft_has_content():
            return True
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr('planning.characters.unsaved_title', 'Nieuw personage niet opgeslagen'))
        box.setText(tr('planning.characters.unsaved_text', 'Je hebt een nieuw personage dat nog niet is opgeslagen.'))
        save = box.addButton(tr('common.save', 'Opslaan'), QMessageBox.AcceptRole)
        discard = box.addButton(tr('common.dont_save', 'Niet opslaan'), QMessageBox.DestructiveRole)
        cancel = box.addButton(tr('common.cancel', 'Annuleren'), QMessageBox.RejectRole)
        box.setDefaultButton(save)
        box.exec()
        if box.clickedButton() is save:
            candidate = self.detail._collect()
            return bool(candidate and self.save_character(candidate))
        if box.clickedButton() is discard:
            self.close_detail()
            return True
        return False

    def delete_character(self, cid):
        char = next((c for c in self.characters if c.id == cid), None)
        if not char: return
        if not confirm(self, tr('planning.characters.delete_title', 'Personage verwijderen'), tr('planning.characters.delete_confirm', '“{name}” verwijderen uit de planning?', name=char.name)): return
        old = copy.deepcopy(self.characters)
        candidate = [copy.deepcopy(c) for c in self.characters if c.id != cid]
        for c in candidate:
            c.relations = [r for r in c.relations if r.target_id != cid]
        result = self.owner.persist_characters(candidate)
        if result == 'failed':
            self.characters = old
            return
        if result == 'disk':
            return
        self.characters = candidate
        self.refresh_list(); self.close_detail(); self.changed.emit()
        if not self.owner.remove_character_from_scenes(cid):
            QMessageBox.warning(
                self,
                tr('planning.characters.scene_cleanup_title', 'Personage verwijderd'),
                tr('planning.characters.scene_cleanup_failed', 'Het personage is verwijderd, maar verwijzingen in scènes konden niet allemaal worden bijgewerkt. Probeer de planning opnieuw op te slaan.'),
            )

    def delete_relation(self, source_id, relation_id):
        before = copy.deepcopy(self.characters)
        source = next((c for c in self.characters if c.id == source_id), None)
        if not source: return
        relation = next((r for r in source.relations if r.id == relation_id), None)
        if not relation: return
        source.relations = [r for r in source.relations if r.id != relation_id]
        target = next((c for c in self.characters if c.id == relation.target_id), None)
        if target and relation.inverse_type:
            target.relations = [r for r in target.relations if not (r.target_id == source.id and r.type.lower() == relation.inverse_type.lower())]
        result = self.owner.persist_characters(self.characters)
        if result == 'mine':
            self.detail.set_character(source, self.characters); self.changed.emit()
        elif result == 'failed':
            self.characters = before; self.refresh_list(source_id)
        # 'disk': adopt_active_book() already reloaded the selected disk state.

    def add_relation(self, source_id, target_id, relation_type):
        before = copy.deepcopy(self.characters)
        source = next((c for c in self.characters if c.id == source_id), None); target = next((c for c in self.characters if c.id == target_id), None)
        if not source or not target: return
        inverse = RELATION_PAIRS.get(relation_type.lower(), '')
        if not any(r.target_id == target.id and r.type.lower() == relation_type.lower() for r in source.relations):
            source.relations.append(Relation(target_id=target.id, type=relation_type, inverse_type=inverse))
        if inverse and not any(r.target_id == source.id and r.type.lower() == inverse.lower() for r in target.relations):
            target.relations.append(Relation(target_id=source.id, type=inverse, inverse_type=relation_type))
        result = self.owner.persist_characters(self.characters)
        if result == 'mine':
            self.detail.set_character(source, self.characters); self.changed.emit()
        elif result == 'failed':
            self.characters = before; self.refresh_list(source_id)
        # 'disk': the central adoption keeps the reloaded disk model intact.
