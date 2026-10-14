# QuietWriter 1.5.0-dev.13

Improved recovery of interrupted fixture directory swaps. A hard crash after the second rename can now be recovered to the previous version. Added standalone tests for rejecting downgrades, replayed version metadata and expired signed manifests. The production updater remains disabled; real release archive compatibility and production signature pinning are still pending.
