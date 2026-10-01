from pathlib import Path

from quietwriter.workspace_path import normalize_workspace_path


def test_relative_workspace_is_never_relative_to_program_directory(monkeypatch, tmp_path):
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    assert normalize_workspace_path('mijnboeken', home / 'QuietWriter') == (home / 'mijnboeken').resolve()


def test_absolute_workspace_is_preserved(tmp_path):
    target = tmp_path / 'books'
    assert normalize_workspace_path(target, tmp_path / 'default') == target.resolve()


def test_openrouter_warmup_is_local_and_nonblocking():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    block = source[source.index('    def ensure_warmup'):source.index('    def _provider_model')]
    assert "provider_name == 'openrouter'" in block
    assert "ConversationStore.entry('assistant'" in block
    assert 'provider.is_available()' not in block


def test_send_does_not_probe_provider_synchronously():
    source = Path('quietwriter/ai/ui.py').read_text(encoding='utf-8')
    block = source[source.index('    def send(self):'):source.index('    def _continue_send')]
    assert 'provider.is_available()' not in block


def test_release_contains_reader_guide_and_real_smoke_mode():
    prep = Path('tools/prepare_release.py').read_text(encoding='utf-8')
    spec = Path('packaging/quietwriter.spec').read_text(encoding='utf-8')
    workflow = Path('.github/workflows/build-windows.yml').read_text(encoding='utf-8')
    app = Path('quietwriter/app.py').read_text(encoding='utf-8')
    assert 'documents/LEESMIJ.txt' in prep
    assert "_file('documents/LEESMIJ.txt', '.')" not in spec
    build = Path('build_exe.cmd').read_text(encoding='utf-8')
    assert 'LEESMIJ.txt" "!OUT!\\LEESMIJ.txt' in build
    assert '--smoke-test' in workflow
    assert "QTimer.singleShot(1500, app.quit)" in app
