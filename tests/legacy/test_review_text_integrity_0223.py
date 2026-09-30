"""Regression coverage for the externally reviewed QuietWriter 0.22.3 fixes.

Pure/source-level tests always run. The two small Qt runtime tests skip cleanly
when PySide6 is unavailable in the test environment.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from quietwriter.media.markup import replace_searchable_text

ROOT = Path(__file__).resolve().parents[2]
EDITOR_SOURCE = ROOT / 'quietwriter' / 'ui' / 'editor_page.py'
SPELL_SOURCE = ROOT / 'quietwriter' / 'ui' / 'spell_panel.py'
SETTINGS_SOURCE = ROOT / 'quietwriter' / 'ui' / 'settings_page.py'
MAIN_SOURCE = ROOT / 'quietwriter' / 'ui' / 'main_window.py'
PUBLICATION_SETUP_SOURCE = ROOT / 'quietwriter' / 'ui' / 'publication' / 'publication_setup.py'


def _method(source: str, name: str, next_name: str) -> str:
    return source.split(f'    def {name}', 1)[1].split(f'    def {next_name}', 1)[0]


def test_replace_searchable_text_preserves_image_path_but_replaces_visible_text():
    source = (
        'assets in gewone tekst.\n\n'
        '![assets in alt](../assets/images/asset-assets.png "assets in onderschrift")\n\n'
        'Nogmaals assets.'
    )
    changed = replace_searchable_text(source, re.compile(re.escape('assets'), re.IGNORECASE), 'spullen')

    assert changed.startswith('spullen in gewone tekst.')
    assert '![spullen in alt]' in changed
    assert '"spullen in onderschrift"' in changed
    assert '(../assets/images/asset-assets.png ' in changed
    assert '../spullen/' not in changed
    assert changed.endswith('Nogmaals spullen.')


def test_replace_all_uses_masked_offset_replacement_helper():
    source = EDITOR_SOURCE.read_text(encoding='utf-8')
    method = _method(source, 'replace_all_matches(self):', '_remember_panel_widths(self, *_):')
    assert 'replace_searchable_text(text, rx, replacement)' in method
    assert 'rx.sub(' not in method


def test_spell_change_validates_stale_offsets_before_mutating_title_or_body():
    source = SPELL_SOURCE.read_text(encoding='utf-8')
    method = _method(source, 'change(self):', 'ignore(self):')
    assert 'text[start:end] != word' in method
    assert '_reanchor_stale_row(source, word, start)' in method
    # Both mutation routes must occur after the validation/re-anchor block.
    validation = method.index('text[start:end] != word')
    assert method.index('chapter_title.setText') > validation
    assert method.index('cur.insertText(replacement)') > validation


def test_structure_conflict_without_chapter_is_visible_and_never_silently_retried():
    source = EDITOR_SOURCE.read_text(encoding='utf-8')
    method = _method(source, '_resolve_external_change(self, exc:', '_handle_concurrency_issue(self, exc:')
    assert 'if not self.chapter:' in method
    assert 'structure_conflict.title' in method
    assert 'publication_editor.has_pending_changes()' in method
    assert 'publication_setup.has_pending_changes()' in method
    assert 'self._adopt_disk_book(None)' in method
    assert 'return False' in method
    # Regression for the reviewed bug: no early chapter guard before UX.
    prefix = method.split('if not self.chapter:', 1)[0]
    assert 'not self.chapter' not in prefix


def test_publication_setup_can_report_unsaved_checkbox_changes():
    source = PUBLICATION_SETUP_SOURCE.read_text(encoding='utf-8')
    assert 'def has_pending_changes(self) -> bool:' in source
    assert 'selected != list(self._data.enabled)' in source


def test_central_book_adopt_refreshes_preserved_publication_setup_state():
    source = EDITOR_SOURCE.read_text(encoding='utf-8')
    method = _method(source, 'adopt_live_book(self, book, preferred_chapter_id: str | None = None):', '_rebuild_word_count_cache(self):')
    assert 'self.content_stack.currentWidget() is self.publication_setup' in method
    assert 'self.publication_setup.set_data(self.publication_store.load(book))' in method


def test_settings_preview_does_not_apply_manuscript_formatting_to_live_editor():
    source = SETTINGS_SOURCE.read_text(encoding='utf-8')
    preview = _method(source, '_preview_appearance(self, *_):', 'restore_preview(self):')
    restore = _method(source, 'restore_preview(self):', 'update_sync_warning(self):')
    assert 'apply_writing_font' not in preview
    assert 'apply_manuscript_style' not in preview
    assert 'apply_writing_font' not in restore
    assert 'apply_manuscript_style' not in restore

    # Font controls may update the settings-local preview card, not the manuscript.
    assert 'self.editor_font.currentTextChanged.connect(self._update_font_preview)' in source
    assert 'self.editor_font_size.valueChanged.connect(self._update_font_preview)' in source


def test_committed_layout_change_cleans_presentation_only_undo_history():
    settings_source = SETTINGS_SOURCE.read_text(encoding='utf-8')
    save = _method(settings_source, 'save_settings(self):', 'begin_session(self):')
    assert 'writing_layout_changed = (' in save
    assert 'new_typography != self.original_typography' in save
    assert 'new_manuscript_style.smart_quotes' not in save.split('writing_layout_changed = (', 1)[1].split(')', 1)[0]
    assert 'settings_saved(old_root, writing_layout_changed=writing_layout_changed)' in save

    main_source = MAIN_SOURCE.read_text(encoding='utf-8')
    applied = _method(main_source, 'settings_saved(self, old_root, writing_layout_changed: bool = False):', 'sync_tool_buttons(self):')
    assert 'if writing_layout_changed:' in applied
    assert 'self.editor_page.editor.reset_undo_history()' in applied
    assert 'self.planning_page.notes_page.editor.reset_undo_history()' in applied


def test_spell_change_reanchors_shifted_occurrence_at_runtime():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    QtWidgets = pytest.importorskip('PySide6.QtWidgets')
    from quietwriter.ui.spell_panel import SpellPanel

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    class Dictionary:
        words = {'goed'}

        @staticmethod
        def misspellings(text):
            return [(m.group(0), m.start(), m.end()) for m in re.finditer(r'\bfout\b', text)]

        @staticmethod
        def suggest(word):
            return ['goed'] if word == 'fout' else []

    class Highlighter:
        def rehighlight(self):
            pass

    class Status:
        def showMessage(self, *_args, **_kwargs):
            pass

    class Main:
        status = Status()

    class Page:
        preview_live_book = None
        main = Main()

        def __init__(self):
            self.dictionary = Dictionary()
            self.chapter_title = QtWidgets.QLineEdit('')
            self.editor = QtWidgets.QTextEdit()
            self.editor.setPlainText('fout hier')
            self.highlighter = Highlighter()

        def rename_current(self):
            pass

    page = Page()
    panel = SpellPanel(page)
    try:
        assert panel.rows == [('body', 'fout', 0, 4)]
        page.editor.setPlainText('nieuw fout hier')
        panel.change()
        assert page.editor.toPlainText() == 'nieuw goed hier'
    finally:
        panel.deleteLater()
        page.editor.deleteLater()
        page.chapter_title.deleteLater()
        app.processEvents()
