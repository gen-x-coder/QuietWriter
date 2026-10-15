from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def test_lab_build_is_onedir_and_keeps_work_outside_onedrive():
    script=(ROOT/'tools/build_updater_lab.cmd').read_text(encoding='utf-8').lower()
    assert '--onedir' in script
    assert '--onefile' not in script
    assert '%temp%' in script
    assert 'updater-lab-onedir' in script
    assert 'if errorlevel 1' in script

def test_acceptance_scripts_select_new_onedir_path():
    frozen=(ROOT/'tools/test_frozen_updater_lab.py').read_text(encoding='utf-8')
    handoff=(ROOT/'tools/test_windows_handoff_dev28.py').read_text(encoding='utf-8')
    assert 'updater-lab-onedir/QuietWriterUpdaterLab/QuietWriterUpdaterLab.exe' in frozen
    assert 'Expected onedir updater EXE' in handoff
    assert 'child.communicate(timeout=15)' in handoff
