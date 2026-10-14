"""Control and restore source-only presentation files from the PUBLIC QuietWriter repo.

Run this in a SOURCE checkout/working directory, not in a frozen Windows distribution.
This does not modify tracked application runtime files and refuses overwriting existing assets.
"""
from __future__ import annotations
import argparse
import hashlib
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ASSETS = {
'branding/screenshots/02-open-punten.png': 'd930370c3bc66790b9d8f4d397a0759369a85266',
'branding/screenshots/03-meelezer.png': 'f2e4ebda2ea58165abeb91235b267410d7bcab96',
'branding/screenshots/04-in-dit-hoofdstuk.png': 'e8e77610eceb00774cffa7baf3e8cf5cb10bba4c',
'branding/screenshots/05-planning-personages.png': '8b2ac30d62c0b957cbbe2c3763a1ccb2ff7212e3',
'branding/screenshots/07-bewaarplaats.png': '5498c842fd9e146733337359f07264264ee73720',
'branding/screenshots/08-versiegeschiedenis.png': 'e3e9a76c42ea50766af69e38021962efabc32989',
'branding/screenshots/11-exporteren.png': '836a45ba38137f03571f7ee9814e64752c248a9c',
'branding/screenshots/13-themas.png': 'aff1bc50980ec8ddf9e25e5c37f158b552e3901b',
'branding/screenshots/hero-met-logo.png': '55efaa6848767f7fded3443b7271261640eff027',
}
BASE = 'https://raw.githubusercontent.com/gen-x-coder/QuietWriter/903625d3d178fd787f520ee3317e302bef01882b/'

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def run(restore=False):
    missing=[];wrong=[];good=[]
    for name,sha in ASSETS.items():
        p=ROOT/name
        if not p.is_file():
            if not restore: missing.append(name);continue
            try:
                req=urllib.request.Request(BASE+name, headers={'User-Agent':'QuietWriter-Source-Audit'})
                with urllib.request.urlopen(req,timeout=30) as r: data=r.read()
                if git_blob(data)!=sha: raise ValueError('Git blob SHA mismatch: '+name)
                p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            except Exception as e:
                print('FETCH FAILED:',name,str(e));missing.append(name);continue
        data=p.read_bytes()
        (good if git_blob(data)==sha else wrong).append(name)
    readme = ROOT / 'README_EN.md'
    if not readme.is_file():
        missing.append('README_EN.md')
    print(f'OK: {len(good)} branding assets; missing: {len(missing)}; changed: {len(wrong)}')
    for name in missing:print('MISSING:',name)
    for name in wrong:print('DIFFERENT:',name)
    return 1 if (missing or wrong) else 0

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--restore-missing',action='store_true');arg=ap.parse_args()
    raise SystemExit(run(arg.restore_missing))
