"""1.7.0 (dev18): echt exportvoorbeeld, zonder iets te onthouden of in de exportmap te zetten."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
pytest.importorskip('PySide6')
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from quietwriter.exporting import preview as preview_module
from quietwriter.storage import Library
from quietwriter.ui import export_preview
from quietwriter.ui.main_window import MainWindow


@pytest.fixture
def env(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(preview_module.tempfile, 'gettempdir', lambda: str(tmp_path / 'tmp'))
    lib = Library(tmp_path / 'ws')
    settings = QSettings(str(tmp_path / 's.ini'), QSettings.IniFormat)
    settings.setValue('spell_enabled', False); settings.setValue('ai_enabled', False)
    out = tmp_path / 'uit'; out.mkdir()
    settings.setValue('export/output_dir', str(out))
    md = '---\ntitle: Haven\nauthor: Lucas\n---\n\n# Een\n\nTekst een met een noot.^[Eerste noot.]\n\n# Twee\n\nTekst twee.\n'
    (tmp_path / 'haven.md').write_text(md, encoding='utf-8')
    book = lib.import_markdown_book(tmp_path / 'haven.md'); lib.track_book(book)
    book = lib.load_book(book.path)
    window = MainWindow(settings, lib, [])
    window.open_book(book); window.show_export(); app.processEvents()
    yield app, window, window.export_page, out, Path(book.path), tmp_path
    window.close()


def test_epub_preview_goes_to_temp_and_shows_chapters_in_order(env):
    app, _w, page, out, book_path, tmp_path = env
    settings_file = book_path / 'export' / 'settings.json'
    before = settings_file.read_bytes() if settings_file.exists() else None
    path = page.show_export_preview('epub', page._settings_from_ui())
    assert path is not None and path.parent.parent == tmp_path / 'tmp' / 'QuietWriter-voorbeeld'
    assert path.name == 'haven-voorbeeld.epub'
    assert list(out.iterdir()) == []                                   # exportmap leeg
    assert (settings_file.read_bytes() if settings_file.exists() else None) == before   # niets onthouden
    dialog = page._preview_window
    assert isinstance(dialog, export_preview.EpubPreviewDialog) and dialog.isVisible()
    text = dialog.browser.toPlainText()
    assert text.index('Tekst een') < text.index('Eerste noot') < text.index('Tekst twee')   # noot staat eronder
    assert 'noot.Eerste' not in text
    dialog.close()


def test_other_formats_open_in_the_users_program(env, monkeypatch):
    app, _w, page, out, _book, tmp_path = env
    opened = []
    monkeypatch.setattr(export_preview.QDesktopServices, 'openUrl', lambda url: opened.append(url.toLocalFile()) or True)
    for fmt, suffix in (('pdf', '.pdf'), ('docx', '.docx'), ('submission', '-manuscript.docx'), ('markdown', '.md')):
        path = page.show_export_preview(fmt, page._settings_from_ui())
        assert path is not None and path.name == f'haven-voorbeeld{suffix}' and path.exists()
    assert len(opened) == 4 and list(out.iterdir()) == []


def test_no_program_says_where_the_preview_is(env, monkeypatch):
    app, _w, page, _out, _book, _tmp = env
    seen = []
    monkeypatch.setattr(export_preview, 'notice_warning', lambda parent, title, text: seen.append(text))
    monkeypatch.setattr(export_preview.QDesktopServices, 'openUrl', lambda url: False)
    path = page.show_export_preview('pdf', page._settings_from_ui())
    assert seen and str(path) in seen[0]


def test_wizard_offers_preview_on_the_export_step_only(env, monkeypatch):
    app, _w, page, out, _book, _tmp = env
    wizard = page.wizard
    calls = []
    monkeypatch.setattr(page, 'show_export_preview', lambda fmt, settings: calls.append((fmt, settings.get('purpose'))))
    wizard.purpose_cards['ereader'].click()
    wizard.go_next(); wizard.go_next(); wizard.go_next()
    wizard.template_cards['literary'].click()
    assert not wizard.extra_button.isVisibleTo(wizard) or wizard.step != 'export'
    wizard.go_next(); assert wizard.step == 'export'
    assert wizard.extra_button.isVisibleTo(wizard) and wizard.extra_button.text() == 'Voorbeeld bekijken'
    wizard.extra_button.click()
    assert calls == [('epub', 'ereader')] and wizard.step == 'export'
    assert list(out.iterdir()) == []


def test_qwbook_has_no_preview(env):
    _app, _w, page, *_ = env
    assert 'qwbook' not in preview_module.PREVIEW_FORMATS
    assert page.run_preview_flow('qwbook', {}) is None


def test_new_preview_never_replaces_an_open_one(env):
    """Review dev19: elk voorbeeld in een eigen map; een vorig (open) voorbeeld blijft ongemoeid."""
    app, _w, page, _out, _book, tmp_path = env
    first = page.run_preview_flow('markdown', page._settings_from_ui())
    content = first.read_bytes()
    second = page.run_preview_flow('markdown', page._settings_from_ui())
    assert first != second and first.parent != second.parent
    assert first.exists() and first.read_bytes() == content


def test_old_preview_folders_are_cleaned_up(env):
    app, _w, page, _out, _book, tmp_path = env
    old = page.run_preview_flow('markdown', page._settings_from_ui())
    stamp = old.parent.stat().st_mtime - preview_module.KEEP_SECONDS - 10
    os.utime(old.parent, (stamp, stamp))
    page.run_preview_flow('markdown', page._settings_from_ui())
    assert not old.parent.exists()


def _epub(path, entries):
    import zipfile
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return path


def test_epub_preview_rejects_references_outside_and_too_large(tmp_path, monkeypatch):
    container = ('<?xml version="1.0"?><container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                 '<rootfiles><rootfile full-path="../buiten.opf"/></rootfiles></container>')
    bad = _epub(tmp_path / 'slecht.epub', {'META-INF/container.xml': container})
    with pytest.raises(preview_module.PreviewError):
        preview_module.epub_preview_page(bad)
    big = _epub(tmp_path / 'groot.epub', {'a.txt': 'x' * 100, 'b.txt': 'y'})
    monkeypatch.setattr(preview_module, 'MAX_UNPACKED_BYTES', 50)
    with pytest.raises(preview_module.PreviewError):
        preview_module.epub_preview_page(big)
    monkeypatch.setattr(preview_module, 'MAX_UNPACKED_BYTES', 10 ** 9)
    monkeypatch.setattr(preview_module, 'MAX_ENTRIES', 1)
    with pytest.raises(preview_module.PreviewError):
        preview_module.epub_preview_page(big)


def test_unreadable_epub_falls_back_to_other_program(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    warnings, opened = [], []
    monkeypatch.setattr(export_preview, 'notice_warning', lambda *a, **k: warnings.append(a))
    bad = _epub(tmp_path / 'leeg.epub', {'x.txt': 'geen e-book'})
    result = export_preview.show_preview(None, bad, 'epub', opener=lambda p: opened.append(p) or True)
    assert result is None and len(warnings) == 1 and opened == [bad]
