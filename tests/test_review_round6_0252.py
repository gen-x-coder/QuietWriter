from pathlib import Path

from quietwriter.book_memory import empty_book_memory, parse_book_memory, render_book_memory
from quietwriter.book_profile import empty_book_profile, parse_book_profile, render_book_profile
from quietwriter.field_merge import merge_scalar_fields
from quietwriter.persona_profile import empty_profile, parse_persona, render_persona

ROOT = Path(__file__).resolve().parents[1]


def _source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_literal_backslashes_before_h2_roundtrip_losslessly():
    samples = ['## kop', r'\## letterlijk', r'\\## twee backslashes', r'\\\## drie backslashes']

    persona = empty_profile(); persona['additional'] = '\n'.join(samples)
    assert parse_persona(render_persona(persona))['additional'] == persona['additional']

    profile = empty_book_profile(); profile['additional'] = '\n'.join(samples)
    assert parse_book_profile(render_book_profile(profile))['additional'] == profile['additional']

    memory = empty_book_memory(); memory['open_points'] = '\n'.join(samples)
    assert parse_book_memory(render_book_memory(memory))['open_points'] == memory['open_points']


def test_three_way_scalar_merge_keeps_local_only_disk_only_and_disk_on_conflict():
    baseline = {'a': 'old-a', 'b': 'old-b', 'c': 'old-c', 'd': 'same'}
    local = {'a': 'local-a', 'b': 'old-b', 'c': 'local-c', 'd': 'same-new'}
    disk = {'a': 'old-a', 'b': 'disk-b', 'c': 'disk-c', 'd': 'same-new'}

    merged, conflicts = merge_scalar_fields(local, baseline, disk, baseline.keys())

    assert merged == {
        'a': 'local-a',
        'b': 'disk-b',
        'c': 'disk-c',
        'd': 'same-new',
    }
    assert conflicts == ['c']


def test_pdf_zeroes_qtextdocument_margin_before_html_layout():
    source = _source('quietwriter/exporting/pdf_exporter.py')
    render = source[source.index('    def render_to'):]
    assert 'qdoc.setDocumentMargin(0)' in render
    assert render.index('qdoc.setDocumentMargin(0)') < render.index('qdoc.setHtml(html_text)')


def test_startup_model_capabilities_are_cached_before_manual_refresh():
    source = _source('quietwriter/ui/settings_page.py')
    init = source[source.index('    def __init__'):source.index('    def _make_settings_page')]
    assert "self._cache_model_capabilities('ollama', supplied_infos.values())" in init
    assert 'def _cache_model_capabilities' in source
    assert 'self._cache_model_capabilities(provider_name, infos)' in source


def test_ai_race_fixtures_define_active_book_before_panel_constructor():
    for rel in ('tests/test_ai_state_qt_runtime_0216.py', 'tests/test_review_ai_scene_qt_0226.py'):
        source = _source(rel)
        before_panel = source[:source.index('        panel = AIPanel(main)')]
        assert "main.active_book = lambda: _active['book']" in before_panel
        assert "_active = {'book': None}" in before_panel
        assert 'lambda: panel.book' not in source


def test_profile_memory_and_details_use_three_way_merge_and_recovery_snapshot():
    profile = _source('quietwriter/ui/book_profile_page.py')
    memory = _source('quietwriter/ui/book_memory_page.py')
    details = _source('quietwriter/ui/book_details.py')

    assert 'merge_scalar_fields(local_profile, self._loaded_profile, disk_profile, keys)' in profile
    assert "{'ai/boekprofiel.md': render_book_profile(local_profile)}" in profile

    assert 'merge_scalar_fields(local_memory, self._loaded_memory, disk_memory, keys)' in memory
    assert "{'ai/memory.md': render_book_memory(local_memory)}" in memory

    assert 'merge_scalar_fields(current, previous, incoming, keys)' in details
    assert "{'book.json': self.library.manifest_text(local_candidate)}" in details
    assert 'Lokale invoer veilig bewaard' in details
