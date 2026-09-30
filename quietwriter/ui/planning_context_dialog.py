from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
)

from ..ai.planning_context import PlanningSelection, options_for_book
from ..i18n import tr


class PlanningContextDialog(QDialog):
    """Choose only the planning material that should accompany an AI request."""

    def __init__(self, parent, library, book, selection: PlanningSelection):
        super().__init__(parent)
        self.library = library
        self.book = book
        self.options = options_for_book(library, book)
        self.setWindowTitle(tr('ai.planning_context.title', 'Planning-context'))
        self.resize(720, 560)

        root = QVBoxLayout(self); root.setContentsMargins(20, 18, 20, 18); root.setSpacing(12)
        info = QLabel(tr(
            'ai.planning_context.info',
            'Kies alleen de Planning-informatie die voor je volgende AI-vragen relevant is. De selectie blijft actief zolang dit boek open is.'
        ))
        info.setObjectName('muted'); info.setWordWrap(True); root.addWidget(info)

        columns = QHBoxLayout(); columns.setSpacing(14)
        self.characters = self._list_column(
            columns, tr('ai.planning_context.characters', 'Personages'),
            [(item.id, item.label, item.id in selection.character_ids) for item in self.options.characters]
        )
        self.scenes = self._list_column(
            columns, tr('ai.planning_context.scenes', 'Scènes'),
            [(item.id, item.label, item.id in selection.scene_ids) for item in self.options.scenes]
        )
        root.addLayout(columns, 1)

        self.error_label = QLabel(self.options.error)
        self.error_label.setObjectName('syncWarning')
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(bool(self.options.error))
        root.addWidget(self.error_label)

        self.notes = QCheckBox(tr('ai.planning_context.notes', 'Planning-notities meenemen'))
        self.notes.setChecked(selection.include_notes and self.options.notes_available)
        self.notes.setEnabled(self.options.notes_available)
        root.addWidget(self.notes)

        hint = QLabel(tr(
            'ai.planning_context.authority',
            'Manuscript = wat daadwerkelijk in het verhaal staat. Planning = wat bedoeld of gepland is. Bij een verschil moet AI dat benoemen.'
        ))
        hint.setObjectName('muted'); hint.setWordWrap(True); root.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('common.done', 'Gereed'))
        buttons.button(QDialogButtonBox.Save).setEnabled(not bool(self.options.error))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('common.cancel', 'Annuleren'))
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def _list_column(self, parent_layout, title: str, rows):
        frame = QFrame(); frame.setObjectName('panel')
        lay = QVBoxLayout(frame); lay.setContentsMargins(10, 10, 10, 10); lay.setSpacing(8)
        label = QLabel(title); label.setObjectName('sectionTitle'); lay.addWidget(label)
        widget = QListWidget(); widget.setAlternatingRowColors(False)
        for item_id, item_label, checked in rows:
            item = QListWidgetItem(item_label)
            item.setData(Qt.UserRole, item_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            widget.addItem(item)
        if not rows:
            empty = QListWidgetItem(tr('ai.planning_context.empty', 'Nog niets in Planning'))
            empty.setFlags(Qt.NoItemFlags); widget.addItem(empty)
        lay.addWidget(widget, 1); parent_layout.addWidget(frame, 1)
        return widget

    @staticmethod
    def _checked_ids(widget: QListWidget) -> set[str]:
        result = set()
        for row in range(widget.count()):
            item = widget.item(row)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                value = item.data(Qt.UserRole)
                if value:
                    result.add(str(value))
        return result

    def selection(self) -> PlanningSelection:
        return PlanningSelection(
            character_ids=self._checked_ids(self.characters),
            scene_ids=self._checked_ids(self.scenes),
            include_notes=bool(self.notes.isChecked()),
        )
