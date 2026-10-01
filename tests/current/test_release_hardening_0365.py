from pathlib import Path


def test_settings_normalizes_workspace_inside_save_not_refresh():
    source = Path('quietwriter/ui/settings_page.py').read_text(encoding='utf-8')
    refresh = source[source.index('    def refresh_models'):source.index('    def resizeEvent')]
    save = source[source.index('    def save_settings'):source.index('    def begin_session')]
    assert 'normalized_workspace =' not in refresh
    assert 'normalized_workspace = str(normalize_workspace_path' in save
    assert "old_root = str(normalize_workspace_path" in save
    assert "'workspace': normalized_workspace" in save


def test_smoke_mode_is_hermetic_and_fails_without_modal_startup_dialog():
    app = Path('quietwriter/app.py').read_text(encoding='utf-8')
    smoke = Path('quietwriter/smoke_test.py').read_text(encoding='utf-8')
    assert 'SmokeTestContext.create() if smoke_test else None' in app
    assert 'QSettings(str(root / "smoke.ini"), QSettings.IniFormat)' in smoke
    assert 'return self.root / "appdata"' in smoke
    assert 'self.errors.append(message)' in smoke
    smoke_except = app[app.index('    except Exception as exc:'):app.index('    exit_code = app.exec()')]
    assert 'if smoke is not None:' in smoke_except
    assert 'return smoke.startup_failed(details)' in smoke_except
    assert 'show_startup_error' in smoke_except


def test_readme_is_copied_next_to_exe_not_into_internal():
    spec = Path('packaging/quietwriter.spec').read_text(encoding='utf-8')
    build = Path('build_exe.cmd').read_text(encoding='utf-8')
    workflow = Path('.github/workflows/build-windows.yml').read_text(encoding='utf-8')
    assert "_file('documents/LEESMIJ.txt', '.')" not in spec
    assert 'copy /y "documents\\LEESMIJ.txt" "!OUT!\\LEESMIJ.txt"' in build
    assert "Join-Path $out 'LEESMIJ.txt'" in workflow
    assert "Join-Path $out '_internal\\LEESMIJ.txt'" in workflow
    assert 'timeout-minutes: 5' in workflow
    assert 'python tools\\check_undefined_names.py || exit /b 1' in build


def test_reader_guide_contains_release_essentials():
    text = Path('documents/LEESMIJ.txt').read_text(encoding='utf-8')
    assert 'Pak de ZIP eerst volledig uit' in text
    assert "'Meer info'" in text and "'Toch uitvoeren'" in text
    assert r'%LOCALAPPDATA%\QuietWriter\QuietWriter\logs\crash.log' in text
    assert r'Documenten\QuietWriter' in text
