from __future__ import annotations

from pathlib import Path


def should_show_first_run(settings, default_workspace: Path, *, force: bool = False) -> bool:
    """Return whether the setup wizard should be shown.

    Existing users are migrated silently: any existing setting, or merely the
    existence of the historical default workspace, marks first-run complete.
    The explicit ``force`` flag is only for deliberate testing and never erases
    existing preferences.
    """
    if force:
        return True
    if settings.value('first_run_requested', False, bool):
        return True
    if settings.value('first_run_done', False, bool):
        return False

    existing_keys = [key for key in settings.allKeys() if key != 'first_run_done']
    if existing_keys or Path(default_workspace).exists():
        settings.setValue('first_run_done', True)
        settings.sync()
        return False
    return True


def request_first_run_reset(settings, workspace: Path) -> None:
    """Reset application preferences while preserving the user's workspace.

    Book/manuscript files live in the workspace and are deliberately untouched.
    The sentinel forces the complete setup on the next launch even though the
    preserved workspace already exists.
    """
    settings.clear()
    settings.setValue('workspace', str(Path(workspace)))
    settings.setValue('first_run_requested', True)
    settings.setValue('first_run_done', False)
    settings.sync()
