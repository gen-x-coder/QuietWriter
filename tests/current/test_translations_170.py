"""1.7.0: Instellingen → Vertalingen, vertalingen van gebruikers, samenvoegtool.
Plus de paneelreparaties (uitlegblok Bewaarplaats, grijze vlakte In dit hoofdstuk)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from quietwriter import i18n

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def user_dir(tmp_path):
    folder = tmp_path / 'translations'
    folder.mkdir()
    i18n.set_user_translation_dir(folder)
    yield folder
    i18n.set_user_translation_dir(None)
    i18n.set_locale('nl')


def test_user_file_adds_a_language_with_english_fallback(user_dir):
    (user_dir / 'it.json').write_text(json.dumps({'_meta': {'code': 'it', 'name': 'Italiano'}, 'common.save': 'Salva'}), encoding='utf-8')
    assert ('it', 'Italiano') in i18n.available_languages()
    assert i18n.set_locale('it') == 'it'
    assert i18n.tr('common.save', 'Opslaan') == 'Salva'
    assert i18n.tr('common.cancel', 'Annuleren') == i18n.builtin_locale('en')['common.cancel']   # Engels als vangnet


def test_user_file_overrides_only_changed_texts_of_a_builtin_language(user_dir):
    (user_dir / 'de.json').write_text(json.dumps({'common.save': 'Sichern', '_meta': {'code': 'de'}}), encoding='utf-8')
    i18n.set_user_translation_dir(user_dir)
    assert i18n.tr('common.save', code='de') == 'Sichern'
    assert i18n.tr('common.cancel', code='de') == i18n.builtin_locale('de')['common.cancel']


def test_without_user_dir_nothing_changes():
    i18n.set_user_translation_dir(None)
    assert [c for c, _ in i18n.available_languages()] == list(i18n.BUILTIN_CODES)
    assert i18n.set_locale('it') == 'nl'


def test_save_payload_keeps_only_differences_for_builtin_languages():
    from quietwriter.ui.translations_page import placeholder_problems, translation_to_save
    base = i18n.builtin_locale('de')
    values = dict(base); values['common.save'] = 'Sichern'; values['common.cancel'] = ''
    assert translation_to_save('de', values) == {'common.save': 'Sichern'}
    assert translation_to_save('it', {'a': 'x', 'b': ' '}) == {'a': 'x'}
    assert placeholder_problems({'k': 'Nog {count} meer'}, {'k': 'Ancora {conto}'}) == ['k']
    assert placeholder_problems({'k': 'Nog {count} meer'}, {'k': '{count} ancora'}) == []


def test_merge_tool_takes_good_texts_and_skips_broken_placeholders(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / 'tools'))
    import merge_translation
    monkeypatch.setattr(merge_translation, 'LOCALES', tmp_path)
    nl = {'common.save': 'Opslaan', 'x.count': 'Nog {count} meer'}
    (tmp_path / 'nl.json').write_text(json.dumps(nl), encoding='utf-8')
    source = tmp_path / 'quietwriter-it.json'
    source.write_text(json.dumps({'_meta': {'code': 'it'}, 'common.save': 'Salva', 'x.count': 'Ancora {conto}',
                                  'onbekend': 'x'}), encoding='utf-8')
    path, taken, skipped = merge_translation.merge(source)
    assert path.name == 'it.json' and taken == 1 and skipped == ['x.count']
    assert json.loads(path.read_text(encoding='utf-8')) == {'common.save': 'Salva'}


@pytest.mark.qt
def test_translations_page_edit_save_export_import(tmp_path, monkeypatch):
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui import translations_page as tp_module
    app = QApplication.instance() or QApplication([])
    shown = []
    monkeypatch.setattr(tp_module, 'notice_information', lambda *a, **k: shown.append(a[-1]))
    monkeypatch.setattr(tp_module, 'notice_warning', lambda *a, **k: shown.append(a[-1]))
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('workspace', str(tmp_path / 'ws'))
    i18n.set_user_translation_dir(None)
    try:
        page = tp_module.TranslationsPage(settings)
        page.target.setCurrentIndex(page.target.findData(tp_module.NEW_LANGUAGE))
        assert page.new_row.isVisibleTo(page)
        page.new_name.setText('Italiano'); page.new_code.setText('it')
        # Eén tekst tegelijk, in een ruim invoerveld; de lijst is alleen om te kiezen.
        page.set_translation('common.save', 'Salva')
        assert page.editor.toPlainText() == 'Salva' and page.ref_text.text() == i18n.builtin_locale('en')['common.save']
        # "Bijhouden" (Track) staat op twee plekken: één keer vertalen geldt voor beide.
        page.set_translation('writing_goal.track_on', 'Monitorare')
        assert page.values['writing_goal.track_today'] == 'Monitorare'
        assert page.shared.isVisibleTo(page)
        page.set_translation('chapter_context.unplanned_title', 'Non pianificato ({conteggio})')
        assert page.editor.property('invalid') is True
        assert page.save()
        saved = json.loads((tmp_path / 'ws' / 'translations' / 'it.json').read_text(encoding='utf-8'))
        assert saved['_meta']['code'] == 'it' and saved['_meta']['name'] == 'Italiano'
        assert saved['common.save'] == 'Salva' and saved['writing_goal.track_today'] == 'Monitorare'
        assert page.target.currentData() == 'it'
        exported = tmp_path / 'quietwriter-it.json'
        monkeypatch.setattr(tp_module.QFileDialog, 'getSaveFileName', staticmethod(lambda *a, **k: (str(exported), '')))
        page.export_file()
        assert json.loads(exported.read_text(encoding='utf-8'))['common.save'] == 'Salva'
        page.set_translation('common.save', '')
        assert page.load_file(exported)
        assert page.values['common.save'] == 'Salva'
        bad = tmp_path / 'kapot.json'; bad.write_text('[1, 2]', encoding='utf-8')
        assert not page.load_file(bad)
        # Vorige/Volgende en "volgende die ontbreekt".
        page.set_translation('common.save', 'Salva')
        row = page.list.currentRow()
        page._step(1); assert page.list.currentRow() == row + 1
        page._step(-1); assert page.list.currentRow() == row
        page._next_open(); assert page._entry_state(page._current) != 'done'
        page.only_missing.setChecked(True)
        visible = [page.entries[r] for r in range(page.list.count()) if not page.list.isRowHidden(r)]
        assert all(page._entry_state(e) != 'done' for e in visible)
        assert any('chapter_context.unplanned_title' in e.keys for e in visible)   # fout blijft zichtbaar
    finally:
        i18n.set_user_translation_dir(None)
        i18n.set_locale('nl')
    assert app is not None


def test_grouping_keeps_different_meanings_apart():
    from quietwriter.ui.translations_page import build_entries
    dutch = {'a.track': 'Bijhouden', 'b.track': 'Bijhouden', 'c.add': 'Toevoegen', 'd.insert': 'Toevoegen'}
    english = {'a.track': 'Track', 'b.track': 'Track', 'c.add': 'Add', 'd.insert': 'Insert'}
    entries = build_entries(sorted(dutch), dutch, {}, english)
    assert sorted(len(e.keys) for e in entries) == [1, 1, 2]


def test_no_language_contains_untranslated_dutch_sentences():
    # 1.7.0: o.a. de back-upinstellingen stonden in het Engels, Duits, Frans en
    # Spaans nog in het Nederlands.
    nl = i18n.builtin_locale('nl')
    markers = (' de ', ' het ', ' een ', ' je ', ' niet ', ' kan ', ' wordt ', 'Bladeren')
    for code in ('en', 'de', 'fr', 'es'):
        data = i18n.builtin_locale(code)
        leftovers = [k for k, v in data.items() if v == nl.get(k) and any(m in f' {v} ' for m in markers)]
        assert leftovers == [], (code, leftovers)


@pytest.mark.qt
def test_wrapped_help_text_never_keeps_an_old_tall_height():
    pytest.importorskip('PySide6')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication
    from quietwriter.ui.panel_help import WrappedLabel
    app = QApplication.instance() or QApplication([])
    label = WrappedLabel('Tekst die je schrapt maar niet kwijt wilt, bewaar je hier. Selecteer een passage en kopieer of knip hem naar de Bewaarplaats.')
    label.resize(36, 10); label.reserve_wrapped_height()
    tall = label.height() if label.maximumHeight() == label.minimumHeight() else label.minimumHeight()
    label.resize(300, label.minimumHeight()); label.reserve_wrapped_height()
    assert label.minimumHeight() < tall and label.minimumHeight() == label.maximumHeight()
    assert app is not None


def test_chapter_context_scroll_area_is_transparent():
    panel = (ROOT / 'quietwriter/ui/chapter_context_panel.py').read_text(encoding='utf-8')
    themes = (ROOT / 'quietwriter/themes.py').read_text(encoding='utf-8')
    assert "setObjectName('chapterContextScroll')" in panel
    assert 'QScrollArea#chapterContextScroll > QWidget > QWidget {{ background: transparent; }}' in themes
