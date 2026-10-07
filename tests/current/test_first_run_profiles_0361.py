from pathlib import Path

from quietwriter.first_run import request_first_run_reset, should_show_first_run
from quietwriter.runtime_profile import parse_runtime_args, profile_for


class FakeSettings:
    def __init__(self, values=None):
        self.values = dict(values or {})
        self.synced = False

    def value(self, key, default=None, type=None):
        value = self.values.get(key, default)
        if type is bool:
            return bool(value)
        return value

    def allKeys(self):
        return list(self.values.keys())

    def setValue(self, key, value):
        self.values[key] = value

    def clear(self):
        self.values.clear()

    def sync(self):
        self.synced = True


def test_profiles_use_separate_settings_and_workspaces(tmp_path):
    prod = profile_for('prod', home=tmp_path)
    dev = profile_for('dev', home=tmp_path)
    assert prod.settings_application == 'QuietWriter'
    assert dev.settings_application == 'QuietWriter-Dev'
    assert prod.default_workspace == tmp_path / 'QuietWriter'
    assert dev.default_workspace == tmp_path / 'QuietWriter-Dev'
    assert prod.app_user_model_id != dev.app_user_model_id


def test_runtime_switches_are_removed_before_qapplication(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    profile, force, qt_argv = parse_runtime_args(['QuietWriter.exe', '--profile', 'dev', '--first-run', '-style', 'fusion'])
    assert profile.key == 'dev'
    assert force is True
    assert qt_argv == ['QuietWriter.exe', '-style', 'fusion']


def test_new_profile_gets_first_run(tmp_path):
    settings = FakeSettings()
    assert should_show_first_run(settings, tmp_path / 'QuietWriter') is True
    assert 'first_run_done' not in settings.values


def test_existing_settings_migrate_without_wizard(tmp_path):
    settings = FakeSettings({'theme': 'Nacht'})
    assert should_show_first_run(settings, tmp_path / 'QuietWriter') is False
    assert settings.values['first_run_done'] is True
    assert settings.synced is True


def test_existing_even_empty_default_workspace_migrates_without_wizard(tmp_path):
    workspace = tmp_path / 'QuietWriter'
    workspace.mkdir()
    settings = FakeSettings()
    assert should_show_first_run(settings, workspace) is False
    assert settings.values['first_run_done'] is True


def test_force_first_run_does_not_mutate_settings(tmp_path):
    settings = FakeSettings({'theme': 'Aurora', 'first_run_done': True})
    before = dict(settings.values)
    assert should_show_first_run(settings, tmp_path / 'QuietWriter', force=True) is True
    assert settings.values == before


def test_reset_request_forces_first_run_even_with_existing_workspace(tmp_path):
    workspace = tmp_path / 'QuietWriter'
    workspace.mkdir()
    settings = FakeSettings({
        'workspace': str(workspace),
        'first_run_done': False,
        'first_run_requested': True,
    })
    assert should_show_first_run(settings, workspace) is True
    assert settings.values['first_run_requested'] is True


def test_reset_preserves_only_workspace_and_requests_setup(tmp_path):
    workspace = tmp_path / 'Mijn Verhalen'
    workspace.mkdir()
    settings = FakeSettings({'theme': 'Nacht', 'ai_enabled': True, 'workspace': 'old'})
    request_first_run_reset(settings, workspace)
    assert settings.values == {
        'workspace': str(workspace),
        'first_run_requested': True,
        'first_run_done': False,
    }
    assert workspace.exists()
    assert settings.synced is True
