from __future__ import annotations

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


def _summary(path: Path) -> tuple[int, int, int]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    tests = failures = errors = 0
    for suite in suites:
        tests += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
    return tests, failures, errors


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="quietwriter-pytest-ci-") as td:
        report = Path(td) / "results.xml"
        cmd = [sys.executable, "-m", "pytest", f"--junitxml={report}", *sys.argv[1:]]
        result = subprocess.run(cmd)

        if result.returncode == 0:
            return 0
        if not report.exists():
            return result.returncode

        try:
            tests, failures, errors = _summary(report)
        except Exception as exc:
            print(f"Kon pytest-resultaat niet controleren: {exc}", file=sys.stderr)
            return result.returncode

        if tests > 0 and failures == 0 and errors == 0:
            print(
                f"Alle {tests} pytest-tests zijn geslaagd; negeer alleen de "
                f"afsluitcode {result.returncode} na de tests (bekend Qt shutdown-probleem)."
            )
            return 0

        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
