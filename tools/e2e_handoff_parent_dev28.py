"""Lab-only launcher in a real separate parent process; does not access user data."""
import os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from quietwriter.update_handoff_windows_lab import ReadyEvent, process_identity

def main():
    work=Path(sys.argv[1]);manifest=Path(sys.argv[2]);updater=Path(sys.argv[3]);fault='--fault-health' in sys.argv[4:]
    with ReadyEvent.create() as event:
        created,image=process_identity(os.getpid())
        cmd=[str(updater),'handoff-update',str(work),'--manifest',str(manifest),
             '--parent-pid',str(os.getpid()),'--parent-created',str(created),
             '--parent-image',image,'--ready-event',event.name]
        if fault:cmd.append('--fault-health')
        # Detached updater log is outside install tree and can be polled by controller.
        log=work.parent/'updater-result.log'
        with log.open('w',encoding='utf-8') as f:
            subprocess.Popen(cmd,cwd=str(work.parent),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,close_fds=True)
        event.await_ready(15)
        print('PARENT READY: updater holds verified process HANDLE',flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
