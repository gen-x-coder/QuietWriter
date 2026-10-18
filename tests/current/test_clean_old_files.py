"""tools/clean_old_files.py: oude bestanden na uitpakken opzij zetten, nooit weggooien."""
import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('clean_old_files', Path('tools/clean_old_files.py'))
mod = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


def test_moves_only_files_missing_from_the_manifest(tmp_path):
    for rel in ('quietwriter/app.py', 'quietwriter/oud_update.py', 'tests/current/test_oud.py',
                'tests/current/test_nieuw.py', 'documents/archive/privé.md', '.venv/lib/x.py',
                'quietwriter/__pycache__/app.cpython-312.pyc'):
        path = tmp_path / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('x', encoding='utf-8')
    (tmp_path / 'SOURCE_MANIFEST.txt').write_text('quietwriter/app.py\ntests/current/test_nieuw.py\n', encoding='utf-8')
    known = mod.known_files(tmp_path)
    old = [p.relative_to(tmp_path).as_posix() for p in mod.old_files(tmp_path, known)]
    assert old == ['quietwriter/oud_update.py', 'tests/current/test_oud.py']
    target = mod.move_aside(mod.old_files(tmp_path, known), tmp_path)
    assert (target / 'quietwriter' / 'oud_update.py').is_file()
    assert not (tmp_path / 'quietwriter' / 'oud_update.py').exists()
    assert (tmp_path / 'documents' / 'archive' / 'privé.md').exists()      # archief blijft
    assert (tmp_path / '.venv' / 'lib' / 'x.py').exists()                   # venv blijft


def test_without_manifest_or_git_nothing_happens(tmp_path):
    (tmp_path / 'quietwriter').mkdir(); (tmp_path / 'quietwriter' / 'a.py').write_text('x')
    assert mod.old_files(tmp_path, known=set()) == []
