from pathlib import Path


def test_notice_copy_is_compact():
    source = (Path(__file__).resolve().parents[2] / 'quietwriter' / 'ai' / 'ui.py').read_text(encoding='utf-8')
    assert 'Nieuw: hoofdstukplanning kan meegaan met AI-vragen. Staat standaard uit.' in source
    assert 'Bij een externe provider verlaten deze gegevens je computer.' in source
    assert 'Zet het hieronder aan als je dat wilt.' not in source


def test_qt_marker_hook_is_registered():
    root = Path(__file__).resolve().parents[2]
    conftest = (root / 'tests' / 'conftest.py').read_text(encoding='utf-8')
    ini = (root / 'pytest.ini').read_text(encoding='utf-8')
    assert 'pytest_collection_modifyitems' in conftest
    assert "'PySide6' in module_file.read_text" in conftest
    assert "'app' in getattr(item, 'fixturenames', ())" in conftest
    assert 'qt: exercises real PySide6/Qt runtime' in ini
