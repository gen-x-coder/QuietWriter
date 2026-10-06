from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QSettings


@dataclass
class SmokeTestContext:
    """Hermetic state for the executable startup smoke test."""

    root: Path
    settings: QSettings
    errors: list[str] = field(default_factory=list)

    @classmethod
    def create(cls) -> "SmokeTestContext":
        root = Path(tempfile.mkdtemp(prefix="quietwriter-smoke-"))
        settings = QSettings(str(root / "smoke.ini"), QSettings.IniFormat)
        settings.setValue("first_run_done", True)
        settings.setValue("workspace", str(root / "workspace"))
        settings.setValue("ai_enabled", False)
        settings.sync()
        return cls(root=root, settings=settings)

    @property
    def local_data(self) -> Path:
        return self.root / "appdata"

    def notify(self, summary: str, details: str, _fingerprint: str = "") -> None:
        message = f"{summary}: {details}".strip(": ")
        self.errors.append(message)
        self._stderr(f"QuietWriter smoke-test fout: {message}")

    def startup_failed(self, details: str) -> int:
        self._stderr(f"QuietWriter smoke-test opstartfout: {details}")
        return 1

    def final_exit_code(self, normal_exit_code: int) -> int:
        return 1 if self.errors else int(normal_exit_code)

    @staticmethod
    def _stderr(message: str) -> None:
        try:
            sys.stderr.write(message + "\n")
            sys.stderr.flush()
        except Exception:
            pass
