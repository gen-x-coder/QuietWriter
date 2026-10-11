from quietwriter.diagnostics import diagnostic_summary

def test_diagnostics_uses_only_allowlisted_runtime_fields():
    result = diagnostic_summary(qt_version='6.test', pyside_version='6.test')
    lines = result.splitlines()
    assert len(lines) == 6
    assert [line.split(':')[0] for line in lines[1:]] == ['QuietWriter', 'Python', 'PySide6', 'Qt', 'Platform']
    assert '6.test' in result

def test_diagnostics_does_not_access_user_files(monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(Path, 'read_text', lambda *a, **k: (_ for _ in ()).throw(AssertionError('accessed private file')))
    assert 'QuietWriter diagnostics' in diagnostic_summary(qt_version='6', pyside_version='6')
