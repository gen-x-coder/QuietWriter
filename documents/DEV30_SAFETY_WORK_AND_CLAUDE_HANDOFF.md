# QuietWriter — snapshot-safety work and Claude handoff

Base: user-supplied local working-tree snapshot (703 files), NOT the incomplete review-candidate ZIP. This snapshot retains README_EN, 9 branding screenshots and local release documents. This is a safety-integration draft, **not a production updater or approved dev.30 release**. Product version metadata intentionally remains at 1.5.0-dev.28 pending verified version reconciliation.

## Implemented on this exact baseline

- `quietwriter/workspace_path.py`: `require_external_user_directory` blocks workspace/backup directories equal to or beneath a frozen portable install tree; normal source checkout has no false install root. Resolves symlinked parents and Windows junctions through `Path.resolve`.
- `ui/workspace_recovery.py`: after initial setup, a missing saved workspace triggers existing visible recovery prompt instead of allowing `Library` to silently create an empty workspace. Re-selected directories must exist. Also blocks a workspace beneath the portable install directory.
- `ui/settings_page.py`: blocks saving workspaces and backup folders beneath the install root; updates default `auto_update_check` to `False`.
- `ui/first_run_wizard.py`: refuses a workspace within install root, including Skip/Finish; does not commit settings when rejected.
- `app.py`: silent update checks default to `False`. The existing manual GitHub flow remains unchanged.
- New focused regression tests `tests/current/test_dev30_workspace_guard.py`. Two existing source-assertion tests updated to new intended semantics.

## Gate / security status

- The `.quietwriter-update-pilot` marker stays workspace-scoped, as the user originally specified. It only reveals an informational pilot button and does NOT authorize installation. If per-device gating becomes a firm product decision, migrate explicitly with tests; do not silently change it.
- `PINNED_RELEASE_KEYS` remains empty; official auto-install remains disabled. No private keys generated, embedded, or published.
- Existing updater scripts remain LAB ONLY. No production sign-off, automatic starter, pointer-swap or crash-independent recovery is claimed.
- Still open: fixed launcher with version folders (O3 architecture), ZIP/SignPath/inventory reconciliation, authentically signed release + offline key ceremony, downgrade/highest-seen enforcement, full installer preflight under lock and recovery, data migration/backups, end-to-end Windows VM testing.

## Local verification

- 30 targeted tests PASS on Linux including new safety guards, startup tests, wizard profile tests, and update defaults.
- `python tools/check_source_assets.py`: 9 assets OK, zero missing/changed.
- Full suite was attempted but exceeded execution time and exhibited at least one failure; **do not call the full suite green**. The prior full suite results (Claude review) belong to the unmodified earlier snapshot.

## Claude review request

Review the changed files on top of the complete local snapshot. Pay particular attention to:
1. `Path.resolve` on Windows junctions, QSettings first-run marker semantics, and whether file missing detection can false-trigger for new first-run workspaces or removable drives.
2. A backup path that is deliberately within a replaceable install and is now rejected by Settings.
3. The manual GitHub update button, the pilot marker and defaults remaining safe.
4. Scope and sequencing of O3 fixed-launcher versioned-install design. Do not approve production automatic installation on the basis of this patch.
5. Run the full test suite on Windows and report every failure, including legacy tests that assert auto-check defaults.
