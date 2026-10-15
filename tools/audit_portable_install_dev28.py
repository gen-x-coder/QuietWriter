"""Read-only local readiness diagnostic; no install/update possible."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from quietwriter.update_install_readiness import audit_portable_install, InstallReadinessError

def main() -> int:
    parser = argparse.ArgumentParser(description='Read-only audit; no install, download or file changes')
    parser.add_argument('installation', type=Path)
    args = parser.parse_args()
    try:
        result = audit_portable_install(args.installation)
    except InstallReadinessError as exc:
        print(f'BLOCKED: {exc}')
        return 2
    print(f"PASS: read-only portable-install audit; files={result['verified_files']}; no changes made")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
