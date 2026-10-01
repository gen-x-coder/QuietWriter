from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class RuntimeProfile:
    key: str
    settings_application: str
    qt_application_name: str
    default_workspace: Path
    app_user_model_id: str


def profile_for(key: str | None = None, *, home: Path | None = None) -> RuntimeProfile:
    value = str(key or os.environ.get('QUIETWRITER_PROFILE', 'prod')).strip().lower()
    if value not in {'prod', 'dev'}:
        value = 'prod'
    home = Path(home or Path.home())
    if value == 'dev':
        return RuntimeProfile(
            key='dev',
            settings_application='QuietWriter-Dev',
            qt_application_name='QuietWriter Dev',
            default_workspace=home / 'QuietWriter-Dev',
            app_user_model_id='LucasBonsel.QuietWriter.Dev',
        )
    return RuntimeProfile(
        key='prod',
        settings_application='QuietWriter',
        qt_application_name='QuietWriter',
        default_workspace=home / 'QuietWriter',
        app_user_model_id='LucasBonsel.QuietWriter',
    )


def parse_runtime_args(argv: list[str]) -> tuple[RuntimeProfile, bool, list[str]]:
    """Parse QuietWriter-only switches and return argv safe for QApplication.

    Supported switches:
    - ``--profile dev|prod`` or ``--profile=dev|prod``
    - ``--first-run`` to show the setup wizard deliberately for testing.

    Unknown arguments are preserved for Qt.
    """
    profile_key: str | None = None
    force_first_run = False
    qt_argv = [argv[0] if argv else 'QuietWriter']
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == '--first-run':
            force_first_run = True
            i += 1
            continue
        if arg == '--profile' and i + 1 < len(argv):
            profile_key = argv[i + 1]
            i += 2
            continue
        if arg.startswith('--profile='):
            profile_key = arg.split('=', 1)[1]
            i += 1
            continue
        qt_argv.append(arg)
        i += 1
    return profile_for(profile_key), force_first_run, qt_argv
