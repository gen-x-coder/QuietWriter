from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ..i18n import tr


class DarlingsActionsPanel(QWidget):
    """Primary editor-side actions for sending a selection to Darlings.

    The context menu and floating selection toolbar remain shortcuts; this panel
    gives the writer a stable, discoverable route in the right tool rail.
    """

    def __init__(self, editor_page):
        super().__init__(editor_page)
        self.editor_page = editor_page
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel(tr('darlings.editor_panel.title', 'Bewaarplaats'))
        title.setObjectName('sectionTitle')
        description = QLabel(tr(
            'darlings.editor_panel.description',
            'Bewaar de huidige selectie als fragment. Kopiëren laat de tekst staan; knippen haalt hem na veilig opslaan uit het manuscript.'
        ))
        description.setObjectName('muted')
        description.setWordWrap(True)
        self.selection_status = QLabel()
        self.selection_status.setObjectName('muted')
        self.selection_status.setWordWrap(True)

        self.copy_button = QPushButton(tr('darlings.copy_action', 'Kopiëren naar bewaarplaats'))
        self.copy_button.setObjectName('secondaryButton')
        self.copy_button.clicked.connect(self.editor_page.copy_selection_to_darlings)
        self.cut_button = QPushButton(tr('darlings.cut_action', 'Knippen naar bewaarplaats'))
        self.cut_button.setObjectName('primaryButton')
        self.cut_button.clicked.connect(self.editor_page.cut_selection_to_darlings)
        self.open_button = QPushButton(tr('darlings.open_library', 'Bewaarplaats openen'))
        self.open_button.setObjectName('secondaryButton')
        self.open_button.clicked.connect(self.editor_page.main.show_darlings)

        root.addWidget(title)
        root.addWidget(description)
        root.addWidget(self.selection_status)
        root.addSpacing(4)
        root.addWidget(self.copy_button)
        root.addWidget(self.cut_button)
        root.addSpacing(8)
        root.addWidget(self.open_button)
        root.addStretch(1)
        self.refresh()

    def refresh(self, *_args):
        editor = self.editor_page.editor
        cursor = editor.textCursor()
        available = bool(
            cursor.hasSelection()
            and not editor.isReadOnly()
            and self.editor_page.book is not None
            and self.editor_page.chapter is not None
            and not self.editor_page.preview_live_book
            and not self.editor_page._chapter_corrupt
            and not editor.selection_intersects_image()
        )
        self.copy_button.setEnabled(available)
        self.cut_button.setEnabled(available)
        if available:
            self.selection_status.setText(tr(
                'darlings.editor_panel.selection_ready',
                'Selectie klaar · kies kopiëren of knippen.'
            ))
        else:
            self.selection_status.setText(tr(
                'darlings.editor_panel.no_selection',
                'Selecteer eerst tekst in het manuscript.'
            ))
