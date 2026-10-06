from __future__ import annotations

import sys
from pyflakes import api, messages, reporter


class UndefinedOnlyReporter(reporter.Reporter):
    def __init__(self) -> None:
        super().__init__(sys.stdout, sys.stderr)
        self.bad: list[str] = []

    def flake(self, message) -> None:
        if isinstance(message, messages.UndefinedName):
            self.bad.append(str(message))

    def syntaxError(self, filename, msg, lineno, offset, text) -> None:
        self.bad.append(f"{filename}:{lineno}:{offset}: {msg}")

    def unexpectedError(self, filename, msg) -> None:
        self.bad.append(f"{filename}: {msg}")


def main() -> int:
    r = UndefinedOnlyReporter()
    api.checkRecursive(["quietwriter"], r)
    if r.bad:
        print("Undefined-name/syntax errors found:", file=sys.stderr)
        for item in r.bad:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("Undefined-name check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
