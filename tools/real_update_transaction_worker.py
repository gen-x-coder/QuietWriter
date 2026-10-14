"""Child-process worker for disposable real-EXE rehearsal only."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from quietwriter.update_real_transaction_lab import swap_worker, recover_worker, finish_worker

def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['swap','recover','commit'])
    p.add_argument('workspace',type=Path)
    p.add_argument('--crash',choices=['staged','old-renamed','new-renamed'])
    a=p.parse_args()
    if a.command=='swap': swap_worker(a.workspace,crash=a.crash)
    elif a.command=='recover': recover_worker(a.workspace)
    else: finish_worker(a.workspace)

if __name__=='__main__': main()
