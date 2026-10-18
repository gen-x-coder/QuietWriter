from __future__ import annotations

import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from ..chapter_context import build_chapter_context
from ..character_mentions import ChapterTextCache, chapter_mentions, plain_text
from ..i18n import tr
from ..planning_storage import PlanningStore
from ..scene_segments import map_scenes, scenes_for_chapter
from ..storage import CorruptSourceError
from ..planning_validation import FuturePlanningFormatError
from .panel_help import PanelHelp


class ChapterContextPanel(QWidget):
    """Read-only Planning context for the live manuscript chapter."""

    openPlanning = Signal()
    jumpToSegment = Signal(int)      # segmentnummer (0 = begin hoofdstuk)
    addUnplanned = Signal()          # ongeplande scènes uit de tekst naar Planning
    markWritten = Signal(str)        # scène-id: status Geschreven (vroeger de knop Planning)

    def __init__(self, library, settings=None):
        super().__init__()
        self.library = library
        self.store = PlanningStore(library)
        self.book = None
        self.chapter_id = None
        self.context = None
        self.segment_map = None
        self.mentions = ()
        self.current_segment = None
        self._texts = ChapterTextCache()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        self.panel_help = PanelHelp(
            settings, 'chapter_context', tr('chapter_context.title', 'In dit hoofdstuk'),
            tr('panel_help.chapter_context_170', 'Hier zie je de scènes uit Planning bij dit hoofdstuk, in dezelfde volgorde als de scènebreuken in je tekst: scène 1 is het stuk vóór de eerste breuk, scène 2 het stuk daarna. Ook zie je welke personages in de tekst voorkomen. Wijzigen doe je in Planning; je tekst blijft onaangeroerd.')
        )
        root.addWidget(self.panel_help)

        self.message = QLabel('')
        self.message.setObjectName('muted')
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.message.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        root.addWidget(self.message)

        self.scroll = QScrollArea()
        self.scroll.setObjectName('chapterContextScroll')   # geen grijze vlakte onder de kaarten
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        # When there are no linked scenes the scroll area is hidden. Keep an
        # explicit expanding filler so the headings stay pinned to the top and
        # the action button stays at the bottom instead of QLabel rows sharing
        # the spare height vertically.
        self.empty_filler = QWidget()
        self.empty_filler.setObjectName('chapterContextFiller')
        self.empty_filler.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.empty_filler, 1)

        self.open_button = QPushButton(tr('chapter_context.open_planning', 'Planning openen'))
        self.open_button.setObjectName('secondaryButton')
        self.open_button.clicked.connect(self.openPlanning.emit)
        root.addWidget(self.open_button)

        self.clear()

    def clear(self, message: str | None = None):
        self.book = None
        self.chapter_id = None
        self.context = None
        self.segment_map = None
        self.mentions = ()
        self._clear_rows()
        self.scroll.hide()
        self.empty_filler.show()
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

    def _book_texts(self, book, chapter_id: str, current_source: str | None) -> list[tuple[str, str]]:
        """Platte tekst van alle hoofdstukken tot en met dit hoofdstuk (boekvolgorde)."""
        rows = []
        for section in getattr(book, 'sections', ()):
            for chapter in section.chapters:
                if chapter.id == chapter_id:
                    if current_source is None:
                        text = self._texts.text(book.path / chapter.file)
                    else:
                        text = plain_text(current_source)
                    rows.append((chapter.id, text))
                    return rows
                rows.append((chapter.id, self._texts.text(book.path / chapter.file)))
        return rows

    def refresh(self, book, chapter_id: str | None, *, available: bool = True,
                current_source: str | None = None, current_segment: int | None = None):
        if not available or book is None or not chapter_id:
            self.clear()
            return

        self.book = book
        self.chapter_id = chapter_id
        self.current_segment = current_segment
        root = self.store.root(book)
        try:
            self._validate_json(root / 'outline.json')
            self._validate_json(root / 'characters.json')
            scenes = self.store.load_scenes(book)
            characters = self.store.load_characters(book)
            context = build_chapter_context(chapter_id, scenes, characters)
            self.context = context
        except FuturePlanningFormatError:
            self.context = None
            self.segment_map = None
            self._clear_rows()
            self.scroll.hide()
            self.empty_filler.show()
            self.message.setText(tr(
                'chapter_context.newer',
                'De opgeslagen Planning is gemaakt met een nieuwere QuietWriter. Werk QuietWriter bij om deze Planning te bekijken.'
            ))
            self.message.show()
            self.open_button.setEnabled(True)
            return
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, CorruptSourceError):
            self.context = None
            self.segment_map = None
            self._clear_rows()
            self.scroll.hide()
            self.empty_filler.show()
            self.message.setText(tr(
                'chapter_context.corrupt',
                'De opgeslagen Planning kan niet betrouwbaar worden gelezen. De editor blijft gewoon beschikbaar.'
            ))
            self.message.show()
            self.open_button.setEnabled(True)
            return

        source = current_source
        if source is None:
            chapter = next((c for s in book.sections for c in s.chapters if c.id == chapter_id), None)
            try:
                source = self.library.read_chapter(book, chapter) if chapter is not None else ''
            except Exception:
                source = ''
        self.segment_map = map_scenes(scenes_for_chapter(scenes, chapter_id), source)
        try:
            self.mentions = chapter_mentions(chapter_id, self._book_texts(book, chapter_id, source), characters)
        except Exception:
            self.mentions = ()

        self._clear_rows()
        self.open_button.setEnabled(True)
        unplanned = self.segment_map.unplanned
        if not context.scenes and not unplanned and not self.mentions:
            self.scroll.hide()
            self.empty_filler.show()
            self.message.setText(tr(
                'chapter_context.empty',
                'Nog geen scènes aan dit hoofdstuk gekoppeld. Voeg of koppel ze in Planning.'
            ))
            self.message.show()
            return

        self.message.hide()
        self.empty_filler.hide()
        self.scroll.show()

        def add(widget):
            self.content_layout.insertWidget(self.content_layout.count() - 1, widget)

        if context.scenes:
            scene_heading = QLabel(tr('chapter_context.scenes_heading', 'Scènes'))
            scene_heading.setObjectName('subsectionTitle')
            add(scene_heading)

        segments = self.segment_map.segments
        for number, scene in enumerate(context.scenes):
            card = QFrame()
            card.setObjectName('chapterContextSceneCard')
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 9, 10, 9)
            card_layout.setSpacing(5)

            heading = QLabel(tr('chapter_context.scene_numbered', '{number}. {title}', number=number + 1,
                                title=scene.title or tr('chapter_context.scene', 'Scène')))
            heading.setObjectName('subsectionTitle')
            heading.setWordWrap(True)
            card_layout.addWidget(heading)
            if current_segment is not None and number == current_segment:
                here = QLabel(tr('chapter_context.you_are_here', '● Hier schrijf je nu'))
                here.setObjectName('contextFieldLabel')
                card_layout.addWidget(here)

            details = []
            if scene.status:
                details.append({
                    'idee': tr('planning.status.idea', 'Idee'),
                    'uitgewerkt': tr('planning.status.developed', 'Uitgewerkt'),
                    'geschreven': tr('planning.status.written', 'Geschreven'),
                }.get(scene.status, scene.status))
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
            # Laat zien welk stuk tekst erbij hoort: zo zie je meteen als de
            # volgorde in Planning en in de tekst uit elkaar loopt.
            if number < len(segments) and segments[number].excerpt:
                excerpt = QLabel(tr('chapter_context.segment_excerpt', 'In de tekst: “{excerpt}”', excerpt=segments[number].excerpt))
                excerpt.setObjectName('muted')
                excerpt.setWordWrap(True)
                card_layout.addWidget(excerpt)

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

            actions = QHBoxLayout()
            actions.setContentsMargins(0, 0, 0, 0)
            if number < len(segments) and (segments[number].has_text or number == len(segments) - 1):
                go = QPushButton(tr('chapter_context.go_to_scene', 'Ga naar deze scène'))
                go.setObjectName('linkButton')
                go.clicked.connect(lambda _=False, index=number: self.jumpToSegment.emit(index))
                actions.addWidget(go)
            else:
                todo = QLabel(tr('chapter_context.not_written_yet', 'Nog niet in de tekst: zet een scènebreuk (***) om eraan te beginnen.'))
                todo.setObjectName('muted')
                todo.setWordWrap(True)
                card_layout.addWidget(todo)
            if scene.status != 'geschreven':
                done = QPushButton(tr('planning.overlay.mark_written', '✓ Klaar'))
                done.setObjectName('linkButton')
                done.setToolTip(tr('planning.overlay.mark_written_tip', 'Markeer deze scène als geschreven'))
                done.clicked.connect(lambda _=False, sid=scene.id: self.markWritten.emit(sid))
                actions.addWidget(done)
            actions.addStretch()
            card_layout.addLayout(actions)

            add(card)

        if unplanned:
            box = QFrame()
            box.setObjectName('chapterContextSceneCard')
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 9, 10, 9)
            box_layout.setSpacing(5)
            title = QLabel(tr('chapter_context.unplanned_title', 'Niet in Planning ({count})', count=len(unplanned)))
            title.setObjectName('subsectionTitle')
            box_layout.addWidget(title)
            for segment in unplanned:
                row = QLabel(tr('chapter_context.unplanned_row', '{number}. {excerpt}', number=segment.index + 1,
                                excerpt=segment.excerpt or '…'))
                row.setObjectName('muted')
                row.setWordWrap(True)
                box_layout.addWidget(row)
            button = QPushButton(tr('chapter_context.add_unplanned', 'Toevoegen aan Planning'))
            button.setObjectName('secondaryButton')
            button.setToolTip(tr('chapter_context.add_unplanned_tip', 'Maakt voor deze stukken tekst een planningscène aan, met status Geschreven. Je tekst verandert niet.'))
            button.clicked.connect(self.addUnplanned.emit)
            box_layout.addWidget(button, 0, Qt.AlignLeft)
            add(box)

        if self.mentions:
            heading = QLabel(tr('chapter_context.in_text_heading', 'Personages in de tekst'))
            heading.setObjectName('subsectionTitle')
            add(heading)
            parts = []
            for mention in self.mentions:
                if mention.first_here:
                    parts.append(tr('chapter_context.mention_first', '{name} ({count}×, voor het eerst)', name=mention.name, count=mention.count))
                else:
                    parts.append(tr('chapter_context.mention', '{name} ({count}×)', name=mention.name, count=mention.count))
            names = QLabel(' · '.join(parts))
            names.setWordWrap(True)
            add(names)
            if any(m.first_here is None for m in self.mentions):
                note = QLabel(tr('chapter_context.mentions_history_unknown', 'Een eerder hoofdstuk kon niet worden gelezen. Daarom staat er niet bij wie hier voor het eerst voorkomt.'))
                note.setObjectName('muted')
                note.setWordWrap(True)
                add(note)

        if context.character_names:
            char_heading = QLabel(tr('chapter_context.characters_heading_planned', 'Personages in Planning'))
            char_heading.setObjectName('subsectionTitle')
            add(char_heading)
            char_names = QLabel(', '.join(context.character_names))
            char_names.setWordWrap(True)
            add(char_names)
