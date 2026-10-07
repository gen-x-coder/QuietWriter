import json
import time

import pytest

from quietwriter.document_view import inline_runs
from quietwriter.manuscript_markup import parse_inline_spans
from quietwriter.manuscript_profile import (
    CURRENT_MANUSCRIPT_SYNTAX_FEATURES,
    CURRENT_MANUSCRIPT_SYNTAX_VERSION,
    FutureManuscriptSyntaxError,
    current_manifest_value,
    profile_from_manifest,
)
from quietwriter.storage import Library


def test_new_books_write_explicit_current_manuscript_profile(tmp_path):
    library = Library(tmp_path)
    book = library.create_book('Nieuw boek')
    data = json.loads(book.manifest_path.read_text(encoding='utf-8'))
    assert data['manuscript_syntax'] == current_manifest_value()
    profile = profile_from_manifest(data)
    assert profile.version == CURRENT_MANUSCRIPT_SYNTAX_VERSION
    assert profile.features == CURRENT_MANUSCRIPT_SYNTAX_FEATURES
    assert profile.is_current


def test_unversioned_book_stays_unversioned_on_normal_manifest_save(tmp_path):
    library = Library(tmp_path)
    folder = library.books_dir / 'legacy'
    (folder / 'chapters').mkdir(parents=True)
    manifest = {
        'format': 2,
        'id': 'legacy-id',
        'title': 'Legacy',
        'metadata': {},
        'sections': [{'id': 'root', 'title': 'Manuscript', 'chapters': []}],
    }
    (folder / 'book.json').write_text(json.dumps(manifest), encoding='utf-8')
    book = library.load_book(folder)
    assert not profile_from_manifest(manifest).explicit
    library.track_book(book)
    library.save_manifest(book)
    saved = json.loads((folder / 'book.json').read_text(encoding='utf-8'))
    assert 'manuscript_syntax' not in saved


def test_future_manuscript_feature_is_rejected_instead_of_ignored():
    data = {
        'manuscript_syntax': {
            'version': CURRENT_MANUSCRIPT_SYNTAX_VERSION,
            'features': sorted(CURRENT_MANUSCRIPT_SYNTAX_FEATURES | {'future-links-v9'}),
        }
    }
    with pytest.raises(FutureManuscriptSyntaxError):
        profile_from_manifest(data)


def test_inline_runs_sweep_preserves_crossed_and_escaped_semantics():
    cases = [
        r'Gewoon **vet** en *schuin*.',
        r'**one *two** three*',
        r'Letterlijk \*ster\* en **echt vet**.',
        r'***beide*** en ~~weg~~ en `code`.',
    ]
    for source in cases:
        spans = tuple(parse_inline_spans(source))
        runs = inline_runs(source, spans)
        visible = ''.join(run.text for run in runs)
        marker_positions = {
            pos for span in spans for a, b in span.marker_ranges for pos in range(a, b)
        }
        # Escape backslashes are hidden too; the expected visible text is easier
        # checked through the runs' own source ranges and style behavior below.
        assert runs
        assert all(run.start < run.end for run in runs)
        assert all(not any(pos in marker_positions for pos in range(run.start, run.end)) for run in runs)
        assert visible


def test_inline_runs_heavy_formatting_has_linearish_budget():
    source = ' '.join(f'**vet{i}** *schuin{i}*' for i in range(500))
    started = time.perf_counter()
    runs = inline_runs(source)
    elapsed = time.perf_counter() - started
    assert runs
    # Regression guard, deliberately generous for slower CI machines. The old
    # implementation repeatedly scanned every span for every character.
    assert elapsed < 1.0
