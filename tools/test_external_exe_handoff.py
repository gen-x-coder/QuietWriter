"""Start a separate worker for a non-destructive EXE health probe.

Usage: python tools/test_external_exe_handoff.py path/to/QuietWriter.exe
This is a rehearsal ONLY; no update installation is performed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main(argv=None):
    parser=argparse.ArgumentParser(description='Independent Windows updater health rehearsal; NO install')
    parser.add_argument('executable',type=Path)
    args=parser.parse_args(argv)
    exe=args.executable.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix='qw-handoff-probe-') as temporary:
        proc=subprocess.run([sys.executable,'-I','-c',
            'import sys; sys.path.insert(0, '+repr(str(ROOT))+'); from quietwriter.update_handoff_probe import main; raise SystemExit(main())',
            '--executable',str(exe),'--health-directory',temporary],
            cwd=str(ROOT),timeout=80,capture_output=True,text=True)
        if proc.stdout: print(proc.stdout,end='')
        if proc.stderr: print(proc.stderr,end='',file=sys.stderr)
        return proc.returncode

if __name__=='__main__': raise SystemExit(main())
