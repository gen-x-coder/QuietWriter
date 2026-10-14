# QuietWriter 1.5 — dev.31 architecture candidate: versioned installation

**Base:** exact user-uploaded 703-file local snapshot plus dev.30 safety changes (705 files). This bundle preserves the complete source tree, README_EN, branding/screenshots and release documents. No public or private GitHub repositories changed. No Windows release generated.

## What is implemented

- `quietwriter/versioned_install.py`: opt-in, separate module for `app-<version>/` folders with a strict `current.json` pointer. Validates an entire *already installed* application folder via `audit_portable_install()` before selecting or activating it. Rejects symlink folders and junctions, invalid names, malformed pointers, missing files and modified bytes.
- Pointer replacement uses same-directory temporary file, fsync and `os.replace`. No removal or rename of the active program folder, so the dangerous empty-folder interval from the old swap design is avoided **within this prototype**.
- `initialize`, `read_active`, `activate_staged`, `read_previous`, `rollback`; previous version remains on disk. A failed candidate validation does not modify the pointer.
- `tools/quietwriter_versioned_starter.py`: proof-of-concept launcher: `--check` validates and prints the target; normal mode launches that verified EXE with shell disabled. This is a Python research utility, **not** yet a frozen native starter.
- `tests/current/test_versioned_install_dev31.py`: standalone contract tests.

## What is deliberately NOT done / blockers

1. **NOT PRODUCTION SAFE.** The local inventory is not a signature or trust anchor. The pointer-switch API is lab-only; no updater or UI calls it. Candidate must be authentic and independently verified before staging. An attacker with local filesystem write access can replace both inventory and files.
2. No OS-wide update lock across validation + activation, no atomic rollback-on-health-failure, no cross-restart reconciliation, no power-failure hard-reset test. `fsync` on the file does not guarantee directory metadata persistence on all filesystems. Corrupt `current.json` fails closed and requires manual recovery.
3. No offline Ed25519 release signing ceremony and no trusted public keys. No trusted downloader, unpacker, version/downgrade restriction or `highest_seen` persistence connected to this prototype.
4. No real Windows fixed-launcher EXE build and no integration with the main application or existing `build_exe.cmd` / SignPath ZIP layout. The current handoff-update lab is separate and must not be mistaken for the new versioned launcher.
5. Existing portable installs, including 1.4.0, retain manual migration through GitHub. User workspaces inside the program directory must be relocated through a reviewed wizard before installing versioned layout. Do not automatically move/delete books.
6. Automatic update checks remain off; the old manual GitHub button is untouched. The empty `.quietwriter-update-pilot` workspace marker continues to show only an informative experimental button, never installation permission.

## Verification in creation environment

- `python -m pytest -q tests/current/test_versioned_install_dev31.py tests/current/test_dev30_workspace_guard.py tests/current/test_update_install_readiness_dev28.py`: **25 passed** in Linux creation environment.
- No full test-suite GO claimed, and no Windows runtime test claimed.

## Claude review request

1. Check for Windows junction/symlink/name and lock races; path collision on case-insensitive filesystems; pointer corruption and power-loss durability.
2. Critique the compatibility of `audit_portable_install` with one-file vs one-dir packaging, and test a candidate containing user books.
3. Decide whether pointer initialization should require external signed release metadata in addition to file inventory. (Recommendation: yes.)
4. Review how to freeze/install the fixed starter independently, keep it outside replaceable versions, and guarantee accessible recovery when `current.json` is damaged.
5. Examine whether `activate_staged` is too permissive for production as currently implemented; it MUST NOT be exposed from user UI. Suggest a single transaction engine with cross-process lock and healthcheck rollback.
6. Verify source integrity of the entire ZIP (9 screenshots, README_EN, release policies, no regression to dev.18 README), run full suite and report differences.

**Acceptance:** This is a version-folder architecture prototype for independent design review, *not* a completed secure updater.
