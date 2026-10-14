from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[2]

def test_entrypoint_is_lab_only_and_requires_manifest():
    s=(ROOT/'tools/quietwriter_updater_lab.py').read_text()
    assert "'handoff-update'" in s
    assert "verify_candidate_file_list(candidate, args.manifest)" in s
    assert s.index('verify_candidate_file_list(candidate, args.manifest)') < s.index('wait_verified_parent(args.parent_pid, args.parent_created, args.parent_image, args.ready_event)', s.index("if args.command == 'handoff-update':"))
    assert s.index('wait_verified_parent(args.parent_pid, args.parent_created, args.parent_image, args.ready_event)', s.index("if args.command == 'handoff-update':")) < s.index('swap_worker(args.workspace, independent_file_manifest=args.manifest)')
    ast.parse(s)

def test_lab_runner_is_temporary_only():
    s=(ROOT/'tools/test_end_to_end_handoff_dev28.py').read_text()
    assert 'TemporaryDirectory' in s and 'copytree' in s and 'NONPRODUCTION-TEST-FIXTURE' in (ROOT/'quietwriter/update_real_transaction_lab.py').read_text()
    ast.parse(s)
