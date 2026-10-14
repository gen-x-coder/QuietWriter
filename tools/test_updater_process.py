"""Dev.9 subprocess smoke test, only disposable non-executable fixtures."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quietwriter.windows_portable_updater import make_test_install, make_test_archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fault', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='qw-process-integration-') as tmp:
        work = Path(tmp)
        install = make_test_install(work)
        (install / 'personal.txt').write_text('keep', encoding='utf-8')
        archive, digest = make_test_archive(work / 'update.zip')
        cmd = [sys.executable, '-m', 'quietwriter.updater_process',
               '--install', str(install), '--archive', str(archive),
               '--sha256', digest, '--simulate-restart']
        if args.fault:
            cmd += ['--fail-after', '1']
        print('Before:', (install / 'version.txt').read_text().strip())
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20)
        version = (install / 'version.txt').read_text().strip()
        print('After:', version)
        if args.fault:
            assert result.returncode != 0 and version == '1.5.0'
            assert not (install / 'test-restarted.flag').exists()
        else:
            assert result.returncode == 0 and version == '1.5.1', result.stderr
            assert (install / 'test-restarted.flag').read_text() == 'restarted'
        assert (install / 'personal.txt').read_text() == 'keep'
        print('PASS: external updater process, disposable files only')


if __name__ == '__main__':
    main()
