from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..chapter_context import build_chapter_context
from ..i18n import tr
from ..planning_storage import PlanningStore
from ..storage import CorruptSourceError
from ..planning_validation import FuturePlanningFormatError


class ChapterContextPanel(QWidget):
    """Read-only Planning context for the live manuscript chapter."""

    openPlanning = Signal()

    def __init__(self, library):
        super().__init__()
        self.store = PlanningStore(library)
        self.book = None
        self.chapter_id = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        title = QLabel(tr('chapter_context.title', 'In dit hoofdstuk'))
        title.setObjectName('sectionTitle')
        intro = QLabel(tr(
            'chapter_context.intro',
            'Opgeslagen scènes en personages uit Planning die aan dit hoofdstuk zijn gekoppeld.'
        ))
        intro.setObjectName('muted')
        intro.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(intro)

        self.message = QLabel('')
        self.message.setObjectName('muted')
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        root.addWidget(self.message)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.open_button = QPushButton(tr('chapter_context.open_planning', 'Planning openen'))
        self.open_button.setObjectName('secondaryButton')
        self.open_button.clicked.connect(self.openPlanning.emit)
        root.addWidget(self.open_button)

        self.clear()

    def clear(self, message: str | None = None):
        self.book = None
        self.chapter_id = None
        self._clear_rows()
        self.scroll.hide()
        self.open_button.setEnabled(False)
        self.message.setText(message or tr(
            'chapter_context.no_chapter',
            'Open een gewoon hoofdstuk om de gekoppelde Planning te bekijken.'
        ))
        self.message.show()

    def _clear_rows(self):
        layout = self.content_layout
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    @staticmethod
    def _validate_json(path):
        if not path.exists():
            return
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(value, dict):
            raise ValueError('verwacht JSON-object')

    def refresh(self, book, chapter_id: str | None, *, available: bool = True):
        if not available or book is None or not chapter_id:
            self.clear()
            return

        self.book = book
        self.chapter_id = chapter_id
        root = self.store.root(book)
        try:
            self._validate_json(root / 'outline.json')
            self._validate_json(root / 'characters.json')
            scenes = self.store.load_scenes(book)
            characters = self.store.load_characters(book)
            context = build_chapter_context(chapter_id, scenes, characters)
        except FuturePlanningFormatError:
            self._clear_rows()
            self.scroll.hide()
            self.message.setText(tr(
                'chapter_context.newer',
                'De opgeslagen Planning is gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij om deze Planning te bekijken.'
            ))
            self.message.show()
            self.open_button.setEnabled(True)
            return
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, CorruptSourceError):
            self._clear_rows()
            self.scroll.hide()
            self.message.setText(tr(
                'chapter_context.corrupt',
                'De opgeslagen Planning kan niet betrouwbaar worden gelezen. De editor blijft gewoon beschikbaar.'
            ))
            self.message.show()
            self.open_button.setEnabled(True)
            return

        self._clear_rows()
        self.open_button.setEnabled(True)
        if not context.scenes:
            self.scroll.hide()
            self.message.setText(tr(
                'chapter_context.empty',
                'Nog geen scènes aan dit hoofdstuk gekoppeld. Voeg of koppel ze in Planning.'
            ))
            self.message.show()
            return

        self.message.hide()
        self.scroll.show()
        if context.character_names:
            char_heading = QLabel(tr('chapter_context.characters_heading', 'Personages'))
            char_heading.setObjectName('subsectionTitle')
            self.content_layout.insertWidget(self.content_layout.count() - 1, char_heading)
            char_names = QLabel(', '.join(context.character_names))
            char_names.setWordWrap(True)
            self.content_layout.insertWidget(self.content_layout.count() - 1, char_names)

        scene_heading = QLabel(tr('chapter_context.scenes_heading', 'Scènes'))
        scene_heading.setObjectName('subsectionTitle')
        self.content_layout.insertWidget(self.content_layout.count() - 1, scene_heading)

        for scene in context.scenes:
            card = QFrame()
            card.setObjectName('chapterContextSceneCard')
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 9, 10, 9)
            card_layout.setSpacing(5)

            heading = QLabel(scene.title or tr('chapter_context.scene', 'Scène'))
            heading.setObjectName('subsectionTitle')
            heading.setWordWrap(True)
            card_layout.addWidget(heading)

            details = []
            if scene.status:
                details.append(scene.status)
            if scene.location:
                details.append(scene.location)
            if details:
                meta = QLabel(' · '.join(details))
                meta.setObjectName('muted')
                meta.setWordWrap(True)
                card_layout.addWidget(meta)

            if scene.synopsis:
                synopsis = QLabel(scene.synopsis)
                synopsis.setWordWrap(True)
                card_layout.addWidget(synopsis)

            for label, value in (
                (tr('chapter_context.goal', 'Doel'), scene.goal),
                (tr('chapter_context.conflict', 'Conflict'), scene.conflict),
                (tr('chapter_context.outcome', 'Uitkomst'), scene.outcome),
                (tr('chapter_context.notes', 'Notities'), scene.notes),
            ):
                if not value:
                    continue
                field_label = QLabel(label)
                field_label.setObjectName('contextFieldLabel')
                card_layout.addWidget(field_label)
                field_value = QLabel(value)
                field_value.setWordWrap(True)
                card_layout.addWidget(field_value)

            if scene.character_names:
                chars = QLabel(tr(
                    'chapter_context.characters',
                    'Personages: {names}', names=', '.join(scene.character_names)
                ))
                chars.setObjectName('muted')
                chars.setWordWrap(True)
                card_layout.addWidget(chars)

            self.content_layout.insertWidget(self.content_layout.count() - 1, card)

