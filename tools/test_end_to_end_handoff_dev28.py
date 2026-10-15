"""Windows-only REAL EXE test: copy two builds, handoff, commit and rollback in temp.

Usage: python tools/test_end_to_end_handoff_dev28.py --current DIR --candidate DIR
No original installation is changed. The frozen updater stays OUTSIDE the test roots.
"""
from __future__ import annotations
import argparse, hashlib, json, os
from pathlib import Path
import shutil, subprocess, sys, tempfile, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from quietwriter.update_real_transaction_lab import MARKER, JOURNAL, _hash_tree


def manifest_of(source: Path, out: Path) -> None:
    files = {}
    for p in source.rglob('*'):
        if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
            raise RuntimeError('Symlink/junction forbidden in test candidate')
        if p.is_file():
            name = p.relative_to(source).as_posix()
            files[name] = {'size': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    if 'QuietWriter.exe' not in files:
        raise RuntimeError('Candidate does not contain QuietWriter.exe')
    out.write_text(json.dumps({'schema': 1, 'files': files}, sort_keys=True), encoding='utf-8')


def scenario(old: Path, new: Path, updater: Path, *, fault: bool):
    with tempfile.TemporaryDirectory(prefix='qw-e2e-handoff-') as td:
        work=Path(td)/'fixture'; work.mkdir()
        (work/MARKER).write_text('NONPRODUCTION-TEST-FIXTURE\n', encoding='ascii')
        manifest=Path(td)/'independent-manifest.json'
        manifest_of(new,manifest)  # trust comes from the read-only source BEFORE staging
        shutil.copytree(old,work/'QuietWriter'); shutil.copytree(new,work/'QuietWriter.next')
        previous=_hash_tree(work/'QuietWriter'); candidate=_hash_tree(work/'QuietWriter.next')
        cmd=[sys.executable, '-I', str(ROOT/'tools'/'e2e_handoff_parent_dev28.py'), str(work), str(manifest),str(updater)]
        if fault:cmd.append('--fault-health')
        result=subprocess.run(cmd,cwd=td,capture_output=True,text=True,timeout=90)
        # Parent logs READY and updater result in its own stdout.
        if result.returncode:
            raise RuntimeError('Lab handoff failed: '+(result.stdout+'\n'+result.stderr)[-1600:])
        if 'PARENT READY' not in result.stdout:
            raise RuntimeError('No READY observed before parent exit')
        deadline=time.monotonic()+45
        log=Path(td)/'updater-result.log'
        expected='LAB HANDOFF UPDATE ROLLED BACK' if fault else 'LAB HANDOFF UPDATE COMMITTED'
        while time.monotonic()<deadline:
            content=log.read_text(encoding='utf-8',errors='replace') if log.exists() else ''
            if expected in content:break
            if 'Traceback' in content or 'Error:' in content:
                raise RuntimeError('Updater failed: '+content[-1600:])
            time.sleep(0.1)
        else:raise RuntimeError('Timed out waiting for updater outcome: '+(content[-1600:] if log.exists() else 'no log'))
        final=_hash_tree(work/'QuietWriter')
        if final != (previous if fault else candidate) or (work/JOURNAL).exists():
            raise RuntimeError('Wrong post-handoff result or journal not cleared')
        print('PASS:', 'health failure rolled back' if fault else 'verified new EXE committed', 'in disposable Windows fixture')


def main():
    a=argparse.ArgumentParser();a.add_argument('--current',required=True,type=Path);a.add_argument('--candidate',required=True,type=Path)
    a.add_argument('--updater',type=Path,default=ROOT/'release/updater-lab-onedir/QuietWriterUpdaterLab/QuietWriterUpdaterLab.exe');opts=a.parse_args()
    if os.name != 'nt':raise SystemExit('Windows-only test')
    old=opts.current.resolve(strict=True);new=opts.candidate.resolve(strict=True);updater=opts.updater.resolve(strict=True)
    if not (old/'QuietWriter.exe').is_file() or not (new/'QuietWriter.exe').is_file():raise SystemExit('Both build folders need QuietWriter.exe')
    if old == new or old in new.parents or new in old.parents:raise SystemExit('Use distinct non-nested build sources')
    for fail in (False,True):scenario(old,new,updater,fault=fail)
    print('PASS: complete Windows lab handoff: READY -> process exit -> verified swap -> health -> commit / rollback')

if __name__=='__main__':main()
