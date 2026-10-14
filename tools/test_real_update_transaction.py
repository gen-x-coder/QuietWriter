"""Two real Windows onedir builds, temporary copies only; no production update."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from quietwriter.update_real_transaction_lab import rehearse_transaction, RehearsalError

def main():
    p=argparse.ArgumentParser(description='Safe, disposable real EXE transaction test')
    p.add_argument('--current',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--fault',choices=['health','staged','old-renamed','new-renamed'])
    a=p.parse_args()
    try:
        result=rehearse_transaction(a.current,a.candidate,fault=a.fault)
        expected='RECOVERED' if a.fault in ('staged','old-renamed','new-renamed') else 'ROLLED_BACK' if a.fault=='health' else 'PASS'
        if result['result']!=expected:
            print('FAIL: unexpected result',result,file=sys.stderr);return 1
        print(f'PASS: {expected}; external transaction worker, original builds untouched')
        return 0
    except (RehearsalError,OSError) as e:
        print(f'FAIL: {e}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
