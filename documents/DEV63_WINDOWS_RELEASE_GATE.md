# Dev.63 – Windows release gate

Based on accepted dev.62. No new product features.

## Findings from full Windows pytest run (14 October 2026)

1176 collected: 1163 passed, 5 failed, 8 skipped; 13 thread warnings.

- OpenRouter test was affected by an actual browser credential present on the host. Test now patches stored_key to an empty value.
- Dictionary source test now decodes source with UTF-8 instead of platform codepage.
- Two symlink tests now skip only when Windows denies symlink creation (WinError 1314); failures for other reasons remain failures.
- SQLite search index test explicitly closes the auxiliary SQLite connection (context manager alone does not close on Windows).
- OpenRouter settings background status/login worker uses a weak bridge reference and ignores a late Qt `RuntimeError` when the dialog has been destroyed.

## Validation

Local Python: 39 targeted tests passed, source compilation succeeded. PySide6 was not available here, so repeat the full test suite on Windows and check for the `Signal source has been deleted` warning. Do not publish a pre-release until the complete Windows suite and EXE smoke test pass.

## Release order

1. Push exact approved source to `gen-x-coder/QuietWriter-dev`.
2. Push the approved source to `gen-x-coder/QuietWriter`.
3. Run `windows-build` workflow on the PUBLIC repository only.
4. Verify artifact `QuietWriter.exe`, frozen smoke test, and portable package.
5. Create GitHub pre-release with release notes and Windows artifact.
