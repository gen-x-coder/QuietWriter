from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSettings, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QFontMetricsF, QPainter, QPen, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import QApplication, QMenu, QTextEdit, QToolButton

from ..manuscript_markup import (ManuscriptStyle, apply_block_style, is_scene_break_line,
                                 selection_format_states, smart_double_quote, toggle_inline)
from ..markdown_io import remove_scene_break
from ..media.markup import image_reference_for_line
from ..themes import THEMES
from ..icon_theme import icon
from ..i18n import tr
from ..typography import WritingTypography, typography_from_values
from .selection_toolbar import SelectionToolbar
from .presentation_highlighter import ManuscriptHighlighter
from .image_block_card import ImageBlockCard


class ManuscriptEditor(QTextEdit):
    imageEditRequested = Signal(int)
    imageDeleteRequested = Signal(int)

    IMAGE_BLOCK_HEIGHT = 132
    """Rustige Markdown-editor met manuscriptweergave en lichte opmaaklaag.

    De bron blijft altijd platte Markdown. De visuele laag gebruikt alleen Qt
    character/block formats; opslaan via ``toPlainText()`` blijft dus volledig
    voorspelbaar en exporteerbaar.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_text_width = 850
        self.min_side_margin = 42
        self.setAcceptRichText(False)
        self._formatting = False
        self._selection_range: tuple[int, int] | None = None
        self._image_resolver = None
        self._image_cards: dict[int, ImageBlockCard] = {}
        self._selected_image_block: int | None = None
        self._image_sync_pending = False
        self._image_layout_pending = False
        self.settings = QSettings('QuietWriter', 'QuietWriter')
        self.typography = WritingTypography.from_settings(self.settings)
        self.manuscript_style = ManuscriptStyle.from_settings(self.settings)

        self._format_timer = QTimer(self)
        self._format_timer.setSingleShot(True)
        self._format_timer.setInterval(90)
        self._format_timer.timeout.connect(self.apply_visual_formatting)

        self._selection_timer = QTimer(self)
        self._selection_timer.setSingleShot(True)
        self._selection_timer.setInterval(1000)
        self._selection_timer.timeout.connect(self._show_selection_toolbar)
        self.selectionChanged.connect(self._selection_changed)
        self.textChanged.connect(self.schedule_formatting)
        self.textChanged.connect(self._schedule_image_sync)
        self.cursorPositionChanged.connect(self._image_cursor_changed)
        self.verticalScrollBar().valueChanged.connect(self._schedule_image_layout)
        self.horizontalScrollBar().valueChanged.connect(self._schedule_image_layout)

        self.selection_toolbar = SelectionToolbar()
        self.selection_toolbar.actionRequested.connect(self.apply_format_action)

        # Scene breaks stay plain Markdown (***), but receive one small hover-only
        # delete affordance. It is a real child control rather than painted text,
        # so hit testing, tooltips and accessibility remain predictable.
        self._hover_scene_block = -1
        self.viewport().setMouseTracking(True)
        # QTextEdit normally supplies an I-beam cursor, but the scene-break
        # hover implementation used to call unsetCursor() on the viewport.
        # On Windows that can fall back to the inherited arrow cursor.  Keep
        # the writing surface explicit: text is always an I-beam; only the
        # small delete affordance below uses a pointing hand.
        self.viewport().setCursor(Qt.IBeamCursor)
        self.scene_delete_button = QToolButton(self.viewport())
        self.scene_delete_button.setObjectName('sceneBreakDelete')
        self.scene_delete_button.setProperty('iconName', 'trash')
        self.scene_delete_button.setIcon(icon('trash', 16))
        self.scene_delete_button.setIconSize(QSize(16, 16))
        self.scene_delete_button.setFixedSize(26, 26)
        self.scene_delete_button.setFocusPolicy(Qt.NoFocus)
        self.scene_delete_button.setCursor(Qt.PointingHandCursor)
        self.scene_delete_button.setToolTip(tr('editor.scene_break.delete', 'Scènebreuk verwijderen'))
        self.scene_delete_button.clicked.connect(self._delete_hovered_scene_break)
        self.scene_delete_button.hide()

        # One non-destructive presentation highlighter owns both Markdown
        # presentation and spelling underlines. Markdown punctuation remains in
        # the source document but is collapsed visually instead of being painted
        # as white/hidden text with normal character width.
        self.presentation_highlighter = ManuscriptHighlighter(self)

        self.apply_typography(self.typography)
        self._update_margins()

    def set_image_resolver(self, resolver):
        """Provide a callable that resolves one managed Markdown reference to a Path."""
        self._image_resolver = resolver
        self._schedule_image_sync()

    def refresh_image_blocks(self):
        self._schedule_image_sync()

    def _schedule_image_sync(self, *_args):
        if self._image_sync_pending:
            return
        self._image_sync_pending = True
        QTimer.singleShot(0, self._sync_image_cards)

    def _sync_image_cards(self):
        self._image_sync_pending = False
        refs = {}
        block = self.document().begin()
        while block.isValid():
            ref = image_reference_for_line(block.text())
            if ref:
                refs[block.blockNumber()] = ref
            block = block.next()

        for number in list(self._image_cards):
            if number not in refs:
                self._image_cards.pop(number).deleteLater()

        theme = self._theme()
        for number, ref in refs.items():
            card = self._image_cards.get(number)
            if card is None:
                card = ImageBlockCard(number, self.viewport())
                card.selected.connect(self._select_image_block)
                card.editRequested.connect(self._edit_image_block)
                card.deleteRequested.connect(self._delete_image_block)
                self._image_cards[number] = card
            asset_path = None
            if self._image_resolver is not None:
                try:
                    asset_path = self._image_resolver(ref.path)
                except Exception:
                    asset_path = None
            card.set_data(ref, asset_path)
            card.set_editable(not self.isReadOnly())
            card.set_theme(theme)
            card.set_selected(number == self._selected_image_block, theme)
        self._schedule_image_layout()

    def _schedule_image_layout(self, *_args):
        if self._image_layout_pending:
            return
        self._image_layout_pending = True
        QTimer.singleShot(0, self._layout_image_cards)

    def _block_viewport_top(self, block) -> int:
        doc_rect = self.document().documentLayout().blockBoundingRect(block)
        cursor = QTextCursor(block)
        caret_rect = self.cursorRect(cursor)
        text_layout = block.layout()
        line_top = 0.0
        if text_layout is not None and text_layout.lineCount() > 0:
            line_top = text_layout.lineAt(0).rect().top()
        viewport_offset = caret_rect.top() - (doc_rect.top() + line_top)
        return round(doc_rect.top() + viewport_offset)

    def _layout_image_cards(self):
        self._image_layout_pending = False
        viewport = self.viewport().rect()
        doc_layout = self.document().documentLayout()
        block = self.document().begin()
        while block.isValid():
            number = block.blockNumber()
            card = self._image_cards.get(number)
            if card is not None:
                doc_rect = doc_layout.blockBoundingRect(block)
                top = self._block_viewport_top(block) + 6
                reserved = max(self.IMAGE_BLOCK_HEIGHT, round(doc_rect.height()))
                height = max(80, min(self.IMAGE_BLOCK_HEIGHT - 12, reserved - 12))
                left = 8
                width = max(260, self.viewport().width() - 16)
                geometry = QRect(left, top, width, height)
                card.setGeometry(geometry)
                card.setVisible(geometry.bottom() >= viewport.top() and geometry.top() <= viewport.bottom())
                if card.isVisible():
                    card.raise_()
            block = block.next()

    def _select_image_block(self, number: int):
        block = self.document().findBlockByNumber(number)
        if not block.isValid() or not image_reference_for_line(block.text()):
            return
        self._selected_image_block = number
        cursor = QTextCursor(block)
        self.setTextCursor(cursor)
        theme = self._theme()
        for n, card in self._image_cards.items():
            card.set_selected(n == number, theme)
        self.setFocus()

    def _edit_image_block(self, number: int):
        self._select_image_block(number)
        self.imageEditRequested.emit(number)

    def _delete_image_block(self, number: int):
        self._select_image_block(number)
        self.imageDeleteRequested.emit(number)

    def _image_cursor_changed(self):
        block = self.textCursor().block()
        number = block.blockNumber() if block.isValid() and image_reference_for_line(block.text()) else None
        if number == self._selected_image_block:
            return
        self._selected_image_block = number
        theme = self._theme()
        for n, card in self._image_cards.items():
            card.set_selected(n == number, theme)

    def current_image_block(self) -> int | None:
        block = self.textCursor().block()
        if block.isValid() and image_reference_for_line(block.text()):
            return block.blockNumber()
        return None

    def selection_intersects_image(self) -> bool:
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        start, end = sorted((cursor.selectionStart(), cursor.selectionEnd()))
        block = self.document().findBlock(start)
        while block.isValid() and block.position() <= end:
            if image_reference_for_line(block.text()):
                return True
            block = block.next()
        return False

    def _move_out_of_image(self, after: bool):
        number = self.current_image_block()
        if number is None:
            return
        block = self.document().findBlockByNumber(number)
        target = block.next() if after else block.previous()
        if not target.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.EndOfBlock)
            cursor.insertBlock()
            target = cursor.block()
        cursor = QTextCursor(target)
        cursor.movePosition(QTextCursor.StartOfBlock if after else QTextCursor.EndOfBlock)
        self.setTextCursor(cursor)

    def _protected_image_message(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            tr('image_block.protected_title', 'Beschermd afbeeldingsblok'),
            tr(
                'image_block.protected_text',
                'Een selectie met een afbeelding wordt niet als gewone tekst aangepast. '
                'Bewerk of verwijder de afbeelding via het afbeeldingsblok.'
            ),
        )

    def cut(self):
        if self.selection_intersects_image():
            self._protected_image_message()
            return
        super().cut()

    def insertFromMimeData(self, source):
        if self.selection_intersects_image():
            self._protected_image_message()
            return
        if self.current_image_block() is not None:
            self._move_out_of_image(after=True)
        super().insertFromMimeData(source)

    def dropEvent(self, event):
        cursor = self.cursorForPosition(event.position().toPoint())
        block = cursor.block()
        if block.isValid() and image_reference_for_line(block.text()):
            event.ignore()
            return
        super().dropEvent(event)

    def setReadOnly(self, read_only: bool):
        super().setReadOnly(read_only)
        self._schedule_image_sync()

    def apply_typography(self, typography: WritingTypography):
        self.typography = typography
        font = typography.body_font()
        self.setFont(font)
        self.document().setDefaultFont(font)
        self.document().markContentsDirty(0, self.document().characterCount())
        if hasattr(self, 'presentation_highlighter'):
            self.presentation_highlighter.rehighlight()
        self.schedule_formatting(immediate=True)
        self.viewport().update()

    def apply_manuscript_style(self, style: ManuscriptStyle):
        self.manuscript_style = style
        if hasattr(self, 'presentation_highlighter'):
            self.presentation_highlighter.rehighlight()
        self.schedule_formatting(immediate=True)

    def reload_manuscript_style(self):
        self.apply_manuscript_style(ManuscriptStyle.from_settings(self.settings))

    def set_editor_font(self, preferred: str, point_size: int | None = None):
        if point_size is None:
            point_size = self.settings.value('editor_font_size', 15, int)
        self.apply_typography(typography_from_values(preferred, point_size))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_margins()
        self._schedule_image_layout()

    def showEvent(self, event):
        super().showEvent(event)
        self._schedule_image_sync()

    def _update_margins(self):
        side = max(self.min_side_margin, (max(0, self.width()) - self.max_text_width) // 2)
        self.setViewportMargins(side, 30, side, 42)

    def schedule_formatting(self, *_args, immediate: bool = False):
        if self._formatting:
            return
        if immediate:
            self._format_timer.stop()
            self.apply_visual_formatting()
        else:
            self._format_timer.start()

    # Compatibility with existing call sites from before the manuscript-style
    # iteration. Scene breaks are now one part of the complete visual pass.
    def apply_scene_break_formatting(self):
        self.schedule_formatting(immediate=True)

    def _theme(self):
        return THEMES.get(str(self.settings.value('theme', 'Helder')), THEMES['Helder'])

    def _selection_changed(self):
        self._selection_timer.stop()
        cursor = self.textCursor()
        if not cursor.hasSelection() or self.isReadOnly():
            self._selection_range = None
            self.selection_toolbar.hide()
            return
        start, end = sorted((cursor.selectionStart(), cursor.selectionEnd()))
        if end <= start:
            return
        self._selection_range = (start, end)
        self._selection_timer.start()

    def _show_selection_toolbar(self):
        if not self._selection_range or self.isReadOnly():
            return
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        end_cursor = QTextCursor(self.document())
        end_cursor.setPosition(self._selection_range[1])
        rect = self.cursorRect(end_cursor)
        text = self.toPlainText()
        start, end = self._selection_range
        self.selection_toolbar.set_states(selection_format_states(text, start, end))
        self.selection_toolbar.adjustSize()
        global_pos = self.viewport().mapToGlobal(QPoint(rect.left(), rect.bottom() + 8))
        screen = QApplication.screenAt(global_pos)
        if screen:
            area = screen.availableGeometry()
            w = self.selection_toolbar.sizeHint().width()
            h = self.selection_toolbar.sizeHint().height()
            x = min(max(global_pos.x(), area.left() + 8), area.right() - w - 8)
            y = global_pos.y()
            if y + h > area.bottom() - 8:
                start_cursor = QTextCursor(self.document())
                start_cursor.setPosition(self._selection_range[0])
                start_rect = self.cursorRect(start_cursor)
                y = self.viewport().mapToGlobal(start_rect.topLeft()).y() - h - 8
            global_pos = QPoint(x, max(area.top() + 8, y))
        self.selection_toolbar.move(global_pos)
        self.selection_toolbar.show()
        self.selection_toolbar.raise_()

    def hide_selection_toolbar(self):
        self._selection_timer.stop()
        self.selection_toolbar.hide()

    def keyPressEvent(self, event):
        self.hide_selection_toolbar()
        modifiers = event.modifiers()
        key = event.key()
        current_image = self.current_image_block()

        if current_image is not None:
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self.imageEditRequested.emit(current_image)
                event.accept(); return
            if key in (Qt.Key_Delete, Qt.Key_Backspace):
                self.imageDeleteRequested.emit(current_image)
                event.accept(); return
            if key == Qt.Key_Left:
                self._move_out_of_image(after=False); event.accept(); return
            if key == Qt.Key_Right:
                self._move_out_of_image(after=True); event.accept(); return
            if event.text() and not (modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)):
                self._move_out_of_image(after=True)
                super().keyPressEvent(event)
                return

        cursor = self.textCursor()
        block = cursor.block()
        if key == Qt.Key_Backspace and not cursor.hasSelection() and cursor.position() == block.position():
            previous = block.previous()
            if previous.isValid() and image_reference_for_line(previous.text()):
                self._select_image_block(previous.blockNumber())
                event.accept(); return
        if key == Qt.Key_Delete and not cursor.hasSelection() and cursor.position() == block.position() + len(block.text()):
            nxt = block.next()
            if nxt.isValid() and image_reference_for_line(nxt.text()):
                self._select_image_block(nxt.blockNumber())
                event.accept(); return

        if self.selection_intersects_image() and (
            key in (Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Return, Qt.Key_Enter)
            or (event.text() and not (modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)))
        ):
            self._protected_image_message()
            event.accept(); return

        # QTextEdit has a long-standing edge case around Return on an empty
        # paragraph that already carries a custom QTextBlockFormat. QuietWriter
        # applies block formats for manuscript line spacing, so the native Return
        # path can briefly create an empty paragraph and then collapse/reformat it
        # on the next layout pass. Insert a real QTextBlock ourselves for ordinary
        # Enter/Return. Besides avoiding that Qt path, this guarantees that two
        # Enters remain two paragraph separators in the plain-Markdown source.
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter)
                and not (modifiers & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier | Qt.ShiftModifier))):
            cursor = self.textCursor()
            cursor.beginEditBlock()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            cursor.insertBlock()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            self.schedule_formatting()
            event.accept()
            return

        if modifiers & Qt.ControlModifier and self.textCursor().hasSelection():
            shortcuts = {Qt.Key_B: 'bold', Qt.Key_I: 'italic', Qt.Key_U: 'underline'}
            if event.key() in shortcuts and not (modifiers & (Qt.AltModifier | Qt.MetaModifier)):
                cursor = self.textCursor(); self._selection_range = (cursor.selectionStart(), cursor.selectionEnd())
                self.apply_format_action(shortcuts[event.key()]); return
            if event.key() == Qt.Key_S and modifiers & Qt.ShiftModifier:
                cursor = self.textCursor(); self._selection_range = (cursor.selectionStart(), cursor.selectionEnd())
                self.apply_format_action('strike'); return
        if (self.manuscript_style.smart_quotes and event.text() == '"'
                and not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier))):
            cursor = self.textCursor()
            if cursor.hasSelection():
                cursor.removeSelectedText()
            quote = smart_double_quote(self.toPlainText(), cursor.position())
            cursor.insertText(quote)
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Extend Qt's normal edit menu with QuietWriter formatting actions.

        The standard Cut/Copy/Paste/Undo actions remain untouched. Formatting is
        added as a compact submenu and uses the same Markdown transformations as
        the floating selection toolbar and keyboard shortcuts.
        """
        self.hide_selection_toolbar()
        cursor = self.textCursor()
        has_selection = bool(cursor.hasSelection() and not self.isReadOnly())
        if has_selection:
            self._selection_range = tuple(sorted((cursor.selectionStart(), cursor.selectionEnd())))

        current_image = self.current_image_block()
        if current_image is not None:
            menu = QMenu(self)
            if not self.isReadOnly():
                edit_action = menu.addAction(tr('image_block.edit', 'Bewerken'))
                delete_action = menu.addAction(tr('image_block.delete', 'Verwijderen'))
                chosen = menu.exec(event.globalPos())
                if chosen is edit_action:
                    self.imageEditRequested.emit(current_image)
                elif chosen is delete_action:
                    self.imageDeleteRequested.emit(current_image)
            else:
                info = menu.addAction(tr('image_block.image', 'Afbeelding'))
                info.setEnabled(False)
                menu.exec(event.globalPos())
            menu.deleteLater()
            return

        if has_selection and self.selection_intersects_image():
            menu = QMenu(self)
            info = menu.addAction(tr('image_block.protected_title', 'Beschermd afbeeldingsblok'))
            info.setEnabled(False)
            menu.exec(event.globalPos())
            menu.deleteLater()
            return

        menu = self.createStandardContextMenu()
        if has_selection:
            menu.addSeparator()
            formatting = menu.addMenu('Opmaak')
            states = selection_format_states(self.toPlainText(), *self._selection_range)

            inline = (
                ('bold', 'Vet'),
                ('italic', 'Cursief'),
                ('underline', 'Onderstrepen'),
                ('strike', 'Doorhalen'),
                ('code', 'Code'),
            )
            for action_name, label in inline:
                action = QAction(label, formatting)
                action.setCheckable(True)
                action.setChecked(bool(states.get(action_name, False)))
                action.triggered.connect(lambda checked=False, a=action_name: self.apply_format_action(a))
                formatting.addAction(action)

            formatting.addSeparator()
            paragraph_menu = formatting.addMenu('Alineastijl')
            blocks = (
                ('paragraph', 'Normale alinea'),
                ('heading', 'Tussenkop'),
                ('quote', 'Citaat'),
                ('bullet', 'Opsomming'),
                ('numbered', 'Genummerde lijst'),
            )
            for action_name, label in blocks:
                action = QAction(label, paragraph_menu)
                action.setCheckable(True)
                action.setChecked(bool(states.get(action_name, False)))
                action.triggered.connect(lambda checked=False, a=action_name: self.apply_format_action(a))
                paragraph_menu.addAction(action)

        menu.exec(event.globalPos())
        menu.deleteLater()

    def apply_format_action(self, action: str):
        if not self._selection_range or self.isReadOnly():
            self.hide_selection_toolbar(); return
        if self.selection_intersects_image():
            self.hide_selection_toolbar()
            self._protected_image_message()
            return
        old = self.toPlainText()
        start, end = self._selection_range
        if action in {'bold', 'italic', 'underline', 'strike', 'code'}:
            new, new_start, new_end = toggle_inline(old, start, end, action)
        elif action in {'paragraph', 'heading', 'bullet', 'numbered', 'quote'}:
            new, new_start, new_end = apply_block_style(old, start, end, action)
        else:
            self.hide_selection_toolbar(); return
        self._replace_changed_text(old, new, new_start, new_end)
        self.hide_selection_toolbar()
        self.setFocus()
        self.presentation_highlighter.rehighlight()
        self.schedule_formatting(immediate=True)

    def _replace_changed_text(self, old: str, new: str, select_start: int, select_end: int):
        if old == new:
            return
        prefix = 0
        max_prefix = min(len(old), len(new))
        while prefix < max_prefix and old[prefix] == new[prefix]:
            prefix += 1
        suffix = 0
        max_suffix = min(len(old) - prefix, len(new) - prefix)
        while suffix < max_suffix and old[len(old)-1-suffix] == new[len(new)-1-suffix]:
            suffix += 1
        old_end = len(old) - suffix
        new_end = len(new) - suffix
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(prefix)
        cursor.setPosition(old_end, QTextCursor.KeepAnchor)
        cursor.insertText(new[prefix:new_end])
        cursor.endEditBlock()
        max_pos = max(0, self.document().characterCount() - 1)
        cursor.setPosition(min(select_start, max_pos))
        cursor.setPosition(min(select_end, max_pos), QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self._selection_range = (min(select_start, max_pos), min(select_end, max_pos))

    def _set_block_format(self, block, kind: str, previous_kind: str | None):
        cursor = QTextCursor(block)
        fmt = QTextBlockFormat()
        fmt.setAlignment(Qt.AlignLeft)
        # PySide6 bindings differ slightly between releases: some accept the
        # enum object here, others require the underlying integer value.
        def enum_value(value):
            return int(value.value) if hasattr(value, 'value') else int(value)

        if kind == 'empty':
            # ProportionalHeight is unreliable for empty QTextBlocks on some Qt
            # 6/Windows combinations: an empty paragraph can visually collapse
            # after the formatting timer runs. Give blank paragraphs a concrete
            # minimum body-line height so a deliberate double-Enter stays visible.
            base_line = QFontMetricsF(self.document().defaultFont()).lineSpacing()
            minimum = max(1.0, base_line * float(self.manuscript_style.line_spacing_percent) / 100.0)
            fmt.setLineHeight(minimum, enum_value(QTextBlockFormat.MinimumHeight))
        elif kind == 'image':
            # The raw Markdown line stays in the QTextDocument, but the writer
            # sees an overlay card. Reserve real layout space for that card.
            fmt.setLineHeight(float(self.IMAGE_BLOCK_HEIGHT), enum_value(QTextBlockFormat.MinimumHeight))
        else:
            fmt.setLineHeight(
                float(self.manuscript_style.line_spacing_percent),
                enum_value(QTextBlockFormat.ProportionalHeight),
            )
        fmt.setBottomMargin(float(self.manuscript_style.paragraph_spacing_px))
        fmt.setTopMargin(0)
        fmt.setLeftMargin(0)
        fmt.setRightMargin(0)
        fmt.setTextIndent(0)

        if kind == 'normal' and previous_kind == 'normal':
            fmt.setTextIndent(float(self.manuscript_style.paragraph_indent_px))
        elif kind == 'heading':
            fmt.setTopMargin(14); fmt.setBottomMargin(10)
        elif kind == 'quote':
            fmt.setLeftMargin(22); fmt.setBottomMargin(10)
        elif kind in {'bullet', 'numbered'}:
            fmt.setLeftMargin(24)
        elif kind == 'scene':
            fmt.setAlignment(Qt.AlignCenter); fmt.setTopMargin(18); fmt.setBottomMargin(18)
        elif kind == 'image':
            fmt.setTopMargin(6); fmt.setBottomMargin(6)
        elif kind == 'empty':
            fmt.setBottomMargin(2)
        if block.blockFormat() != fmt:
            cursor.setBlockFormat(fmt)

    @staticmethod
    def _block_kind(text: str) -> str:
        stripped = text.strip()
        if not stripped:
            return 'empty'
        if is_scene_break_line(text):
            return 'scene'
        if image_reference_for_line(text):
            return 'image'
        if text.startswith('## '):
            return 'heading'
        if text.startswith('> '):
            return 'quote'
        if re.match(r'^[-*]\s+', text):
            return 'bullet'
        if re.match(r'^\d+\.\s+', text):
            return 'numbered'
        return 'normal'

    def apply_visual_formatting(self):
        """Apply layout-only manuscript formatting.

        Inline Markdown presentation is handled by ManuscriptHighlighter.  Keeping
        the two layers separate is important: block layout may change indentation
        and line spacing, while the highlighter can hide Markdown punctuation
        without modifying document contents or the undo stack.
        """
        if self._formatting:
            return
        self._formatting = True
        signals_were_blocked = self.signalsBlocked()
        self.blockSignals(True)
        old = self.textCursor()
        old_pos, old_anchor = old.position(), old.anchor()
        try:
            previous_kind = None
            block = self.document().begin()
            while block.isValid():
                kind = self._block_kind(block.text())
                self._set_block_format(block, kind, previous_kind)
                previous_kind = kind
                block = block.next()
        finally:
            max_pos = max(0, self.document().characterCount() - 1)
            restore = QTextCursor(self.document())
            restore.setPosition(min(old_anchor, max_pos))
            restore.setPosition(min(old_pos, max_pos), QTextCursor.KeepAnchor)
            self.setTextCursor(restore)
            self.blockSignals(signals_were_blocked)
            self._formatting = False
            self.viewport().update()
            self._schedule_image_sync()

    def _scene_break_button_position(self, block):
        cursor = QTextCursor(block)
        rect = self.cursorRect(cursor)
        width = self.viewport().width()
        center = width // 2
        extent = min(180, max(70, width // 4))
        x = min(width - self.scene_delete_button.width() - 8, center + extent + 12)
        y = rect.center().y() + max(4, rect.height() // 2) - self.scene_delete_button.height() // 2
        return QPoint(max(8, x), max(0, y))

    def _update_scene_break_hover(self, pos: QPoint):
        cursor = self.cursorForPosition(pos)
        block = cursor.block()
        if block.isValid() and is_scene_break_line(block.text()):
            number = block.blockNumber()
            if self._hover_scene_block != number:
                self._hover_scene_block = number
            self.scene_delete_button.move(self._scene_break_button_position(block))
            self.scene_delete_button.show()
            self.scene_delete_button.raise_()
            self.viewport().setCursor(Qt.IBeamCursor)
            return
        self._hover_scene_block = -1
        self.scene_delete_button.hide()
        self.viewport().setCursor(Qt.IBeamCursor)

    def mouseMoveEvent(self, event):
        self._update_scene_break_hover(event.position().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        # Do not hide while the pointer moves from the viewport onto the child
        # delete button itself. The button will disappear on the next viewport
        # move or after deletion.
        if not self.scene_delete_button.underMouse():
            self._hover_scene_block = -1
            self.scene_delete_button.hide()
            self.viewport().setCursor(Qt.IBeamCursor)
        super().leaveEvent(event)

    def _delete_hovered_scene_break(self):
        number = self._hover_scene_block
        if number < 0:
            return
        block = self.document().findBlockByNumber(number)
        if not block.isValid() or not is_scene_break_line(block.text()):
            self.scene_delete_button.hide()
            self._hover_scene_block = -1
            return

        text = self.toPlainText()
        new_text, caret = remove_scene_break(text, block.position())
        if new_text == text:
            self.scene_delete_button.hide()
            self._hover_scene_block = -1
            return

        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.Document)
        cursor.insertText(new_text)
        cursor.setPosition(min(caret, len(new_text)))
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self._hover_scene_block = -1
        self.scene_delete_button.hide()
        self.setFocus()

    def paintEvent(self, event):
        super().paintEvent(event)
        theme = self._theme()
        for card in self._image_cards.values():
            card.set_theme(theme)
        # Scene breaks are stored as literal *** but rendered as a quiet divider.
        painter = QPainter(self.viewport())
        color = QColor(theme['muted'])
        color.setAlpha(145)
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        block = self.document().begin()
        while block.isValid():
            text = block.text()
            kind = self._block_kind(text)
            cursor = QTextCursor(block)
            rect = self.cursorRect(cursor)
            if kind == 'scene':
                y = rect.center().y() + max(4, rect.height() // 2)
                width = self.viewport().width()
                center = width // 2
                gap = 48
                extent = min(180, max(70, width // 4))
                painter.drawLine(center - extent, y, center - gap, y)
                painter.drawLine(center + gap, y, center + extent, y)
                painter.drawText(center - 28, y - 8, 56, 16, Qt.AlignCenter, '•  •  •')
            elif kind == 'bullet':
                painter.drawText(rect.left() - 22, rect.top(), 16, rect.height(), Qt.AlignRight | Qt.AlignVCenter, '•')
            elif kind == 'numbered':
                m = re.match(r'^(\d+)\.\s+', text)
                if m:
                    painter.drawText(rect.left() - 36, rect.top(), 30, rect.height(), Qt.AlignRight | Qt.AlignVCenter, m.group(1) + '.')
            elif kind == 'quote':
                painter.drawLine(rect.left() - 13, rect.top() + 2, rect.left() - 13, rect.bottom() - 2)
            block = block.next()
        painter.end()
