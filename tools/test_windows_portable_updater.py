"""Windows-updater transaction demonstration against disposable fixture only."""
import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quietwriter.windows_portable_updater import (make_test_install, make_test_archive,
                                                   update_test_install, PortableUpdateError)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fault', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='quietwriter-windows-updater-') as tmp:
        work = Path(tmp)
        install = make_test_install(work)
        (install / 'personal.txt').write_text('unchanged', encoding='utf-8')
        archive, digest = make_test_archive(work / 'package.zip')
        print('Before:', (install / 'version.txt').read_text().strip())
        try:
            update_test_install(install, archive, expected_sha256=digest,
                                fail_after=1 if args.fault else None)
        except PortableUpdateError as exc:
            print('Simulated failure:', exc)
            if not args.fault:
                raise
        version = (install / 'version.txt').read_text().strip()
        print('After:', version)
        assert version == ('1.5.0' if args.fault else '1.5.1')
        assert (install / 'personal.txt').read_text() == 'unchanged'
        print('PASS: disposable install only; user file preserved')


if __name__ == '__main__':
    main()
