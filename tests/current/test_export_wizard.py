"""Begeleid exporteren: pure logic (no Qt). See documents/QUIETWRITER_ONTWERP_EXPORTWIZARD.md §5."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from quietwriter.exporting import ExportSettingsStore, build_export_document, export_markdown, run_preflight
from quietwriter.exporting.purposes import PURPOSES, apply_purpose, steps_for
from quietwriter.exporting.runner import destination_for, run_export
from quietwriter.exporting.summary import build_content_summary, build_package_summary, round_words
from quietwriter.media.markup import count_words
from quietwriter.qwbook_io import export_qwbook, import_qwbook
from quietwriter.storage import Library


def _book(tmp_path: Path, name='ws'):
    lib = Library(tmp_path / name)
    md = '---\ntitle: Haven\nauthor: Lucas\n---\n\n# Een\n\nEen twee drie vier.\n\n# Twee\n\nVijf zes zeven.\n'
    source = tmp_path / f'{name}.md'
    source.write_text(md, encoding='utf-8')
    book = lib.import_markdown_book(source)
    lib.track_book(book)
    return lib, book


def test_purposes_are_stable_and_map_to_known_formats():
    ids = [purpose.id for purpose in PURPOSES]
    assert ids == ['ereader', 'print', 'word', 'share', 'backup', 'website']
    assert all(purpose.id.isascii() for purpose in PURPOSES)
    assert {purpose.format for purpose in PURPOSES} == {'epub', 'pdf', 'docx', 'qwbook', 'markdown'}
    for purpose in PURPOSES:
        steps = steps_for(purpose.id)
        assert steps[0] == 'purpose' and steps[-1] == 'export'
        assert len(steps) == (5 if purpose.format in ('epub', 'pdf') else 4)


def test_apply_purpose_sets_privacy_defaults_and_keeps_earlier_choices():
    saved = {'format': 'pdf', 'epub': {'template': 'literary'}, 'qwbook': {'include_history': True, 'include_ai_chat': True}}
    share = apply_purpose(saved, 'share')
    assert share['format'] == 'qwbook' and share['purpose'] == 'share'
    assert share['qwbook'] == {'include_history': False, 'include_ai_chat': False}
    backup = apply_purpose(saved, 'backup')
    assert backup['qwbook'] == {'include_history': True, 'include_ai_chat': True}
    ereader = apply_purpose(saved, 'ereader')
    assert ereader['epub']['template'] == 'literary'
    assert saved['format'] == 'pdf', 'input must not be mutated'
    with pytest.raises(ValueError):
        apply_purpose(saved, 'unknown')


def test_settings_store_roundtrips_purpose_and_ai_chat_option(tmp_path):
    lib, book = _book(tmp_path)
    store = ExportSettingsStore(lib)
    settings = store.load(book)
    settings['purpose'] = 'share'
    settings['qwbook'] = {'include_history': False, 'include_ai_chat': False}
    store.save(book, settings)
    again = ExportSettingsStore(lib).load(lib.load_book(book.path))
    assert again['purpose'] == 'share'
    assert again['qwbook'] == {'include_history': False, 'include_ai_chat': False}
    # Unknown purposes are never persisted or loaded.
    raw = json.loads(store.path(book).read_text(encoding='utf-8'))
    raw['purpose'] = 'rocket'
    store.path(book).write_text(json.dumps(raw), encoding='utf-8')
    lib.refresh_book_revision(book)
    assert store.load(book)['purpose'] is None


def test_content_summary_matches_word_count_and_structure(tmp_path):
    lib, book = _book(tmp_path)
    document = build_export_document(lib, book)
    summary = build_content_summary(document)
    expected = sum(count_words(chapter.markdown) for section in document.sections for chapter in section.chapters)
    assert summary.words == expected
    assert summary.chapters == document.chapter_count == 2
    assert summary.images == 0 and summary.has_cover is False
    assert sum(section.chapters for section in summary.sections) == 2
    assert round_words(82_437) == 82_400 and round_words(950) == 950


def test_package_summary_is_read_only(tmp_path):
    lib, book = _book(tmp_path)
    history = lib.archive_dir / book.id
    assert not history.exists()
    before = sorted(p.relative_to(lib.root).as_posix() for p in lib.root.rglob('*'))
    summary = build_package_summary(lib, book)
    after = sorted(p.relative_to(lib.root).as_posix() for p in lib.root.rglob('*'))
    assert before == after, 'looking must never create files or folders'
    assert not history.exists()
    assert summary.history_versions == 0 and summary.history_bytes == 0
    lib.create_version(book, 'manual')
    summary = build_package_summary(lib, lib.load_book(book.path))
    assert summary.history_versions == 1 and summary.history_bytes > 0
    assert summary.history_files > 0


def test_qwbook_can_leave_out_the_reader_conversation(tmp_path):
    lib, book = _book(tmp_path)
    chat = Path(book.path) / '.quietwriter' / 'ai_chat.json'
    chat.parent.mkdir(parents=True, exist_ok=True)
    chat.write_text('[{"role":"user","content":"geheim"}]', encoding='utf-8')
    without = export_qwbook(lib, lib.load_book(book.path), tmp_path / 'zonder.qwbook', include_ai_chat=False)
    with zipfile.ZipFile(without) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('qwbook.json'))
    assert not any('ai_chat' in name for name in names)
    assert manifest['ai_chat_included'] is False
    imported = import_qwbook(Library(tmp_path / 'dest'), without)
    assert not (Path(imported.path) / '.quietwriter' / 'ai_chat.json').exists()
    with_chat = export_qwbook(lib, lib.load_book(book.path), tmp_path / 'met.qwbook')
    with zipfile.ZipFile(with_chat) as archive:
        assert 'book/.quietwriter/ai_chat.json' in archive.namelist()


def test_qwbook_ai_chat_exclusion_also_strips_history_snapshots(tmp_path):
    lib, book = _book(tmp_path)
    chat = Path(book.path) / '.quietwriter' / 'ai_chat.json'
    chat.parent.mkdir(parents=True, exist_ok=True)
    chat.write_text('[{"role":"user","content":"historisch geheim"}]', encoding='utf-8')
    lib.refresh_book_revision(book)
    lib.create_version(book, 'manual')

    package = build_package_summary(lib, lib.load_book(book.path))
    assert package.history_ai_chat_files >= 1
    assert package.history_ai_chat_bytes > 0
    without = export_qwbook(
        lib, lib.load_book(book.path), tmp_path / 'zonder-historische-chat.qwbook',
        include_history=True, include_ai_chat=False,
    )
    with zipfile.ZipFile(without) as archive:
        names = archive.namelist()
        manifest = json.loads(archive.read('qwbook.json'))
        payload = b'\n'.join(archive.read(name) for name in names if not name.endswith('/'))
    assert not any(name.endswith('/.quietwriter/ai_chat.json') or name == 'book/.quietwriter/ai_chat.json' for name in names)
    assert b'historisch geheim' not in payload
    assert manifest['ai_chat_included'] is False
    assert not any(path.endswith('/.quietwriter/ai_chat.json') for path in manifest['history_files'])


def test_preflight_counts_history_files_and_privacy_filter(tmp_path, monkeypatch):
    lib, book = _book(tmp_path)
    chat = Path(book.path) / '.quietwriter' / 'ai_chat.json'
    chat.parent.mkdir(parents=True, exist_ok=True)
    chat.write_text('[]', encoding='utf-8')
    lib.refresh_book_revision(book)
    lib.create_version(book, 'manual')
    package = build_package_summary(lib, lib.load_book(book.path))
    document = build_export_document(lib, lib.load_book(book.path))
    import quietwriter.qwbook_io as qwbook_io

    # With history included the preflight must use the complete projected file count.
    monkeypatch.setattr(qwbook_io, 'MAX_FILE_COUNT', package.book_files)
    settings = {'qwbook': {'include_history': True, 'include_ai_chat': True}}
    assert not run_preflight(document, 'qwbook', settings, package).can_export

    # Excluding both history and Reader chat reduces the projected count accordingly.
    settings = {'qwbook': {'include_history': False, 'include_ai_chat': False}}
    assert run_preflight(document, 'qwbook', settings, package).can_export


def test_runner_renders_the_same_bytes_as_the_direct_exporter(tmp_path):
    lib, book = _book(tmp_path)
    document = build_export_document(lib, book)
    settings = ExportSettingsStore(lib).load(book)
    direct = tmp_path / 'direct.md'
    export_markdown(document, direct, settings)
    result = run_export(lib, book, document, 'markdown', settings, tmp_path / 'runner.md')
    assert result.path.read_bytes() == direct.read_bytes()
    assert result.format == 'markdown' and result.bytes == direct.stat().st_size
    assert destination_for(tmp_path, document, 'epub').name == f'{document.slug}.epub'
    qw = run_export(lib, book, document, 'qwbook', {'qwbook': {'include_history': False, 'include_ai_chat': False}}, tmp_path / 'b.qwbook')
    with zipfile.ZipFile(qw.path) as archive:
        manifest = json.loads(archive.read('qwbook.json'))
    assert manifest['history_included'] is False and manifest['ai_chat_included'] is False
    with pytest.raises(ValueError):
        run_export(lib, book, document, 'odt', settings, tmp_path / 'x.odt')


def test_preflight_blocks_qwbook_over_the_package_limit(tmp_path, monkeypatch):
    lib, book = _book(tmp_path)
    document = build_export_document(lib, book)
    package = build_package_summary(lib, book)
    settings = {'qwbook': {'include_history': True, 'include_ai_chat': True}}
    assert run_preflight(document, 'qwbook', settings, package).can_export
    import quietwriter.qwbook_io as qwbook_io
    monkeypatch.setattr(qwbook_io, 'MAX_TOTAL_SIZE', 10)
    report = run_preflight(document, 'qwbook', settings, package)
    assert not report.can_export
    assert any(item.key == 'qwbook_over_limit' for item in report.items)


def test_export_wizard_navigation_width_and_card_resize_contract():
    source = Path('quietwriter/ui/export_wizard.py').read_text(encoding='utf-8')
    assert "self.action_bar.setMaximumWidth(820 + 84)" in source
    assert 'def resizeEvent(self, event):' in source
    assert 'layout.heightForWidth(self.width())' in source


def test_ui_reference_documents_page_and_modal_wizard_navigation():
    source = Path('documents/UI_REFERENCE.md').read_text(encoding='utf-8')
    assert 'binnen een pagina met scrollende inhoud' in source
    assert 'Korte modale wizards' in source


def test_export_header_and_step_bar_follow_content_width():
    export_page = Path('quietwriter/ui/export_page.py').read_text(encoding='utf-8')
    wizard = Path('quietwriter/ui/export_wizard.py').read_text(encoding='utf-8')
    assert "header.setMaximumWidth(820 + 84)" in export_page
    assert "bar_host.setMaximumWidth(820 + 84)" in wizard
    assert "self.action_bar.setMaximumWidth(820 + 84)" in wizard
    assert "host.setMaximumWidth(820 + 84)" in wizard
