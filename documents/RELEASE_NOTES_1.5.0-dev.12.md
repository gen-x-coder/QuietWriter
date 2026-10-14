# QuietWriter 1.5.0-dev.12

The isolated updater test environment now uses an operating-system lock rather than a permanent lockfile. If the updater process crashes, the lock is released automatically. Recovering an interrupted folder swap also requires the same lock. If both old and new installations exist after an interruption, they are preserved for manual review; automatic health validation is a future milestone. No production updater is enabled.
