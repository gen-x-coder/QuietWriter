from __future__ import annotations

from collections.abc import Iterable, Mapping


def merge_scalar_fields(
    local: Mapping[str, object],
    baseline: Mapping[str, object],
    disk: Mapping[str, object],
    keys: Iterable[str],
) -> tuple[dict[str, object], list[str]]:
    """Three-way merge simple form fields without silently overwriting disk edits.

    Local-only edits stay local, disk-only edits follow disk, and when both sides
    changed the same field differently the disk value wins in the live form.  The
    caller receives the conflicting keys so it can preserve the complete local
    form in Version History before adopting the disk value.
    """
    merged: dict[str, object] = {}
    conflicts: list[str] = []
    for key in keys:
        local_value = local.get(key, '')
        baseline_value = baseline.get(key, '')
        disk_value = disk.get(key, '')
        local_changed = local_value != baseline_value
        disk_changed = disk_value != baseline_value

        if local_changed and disk_changed and local_value != disk_value:
            merged[key] = disk_value
            conflicts.append(key)
        elif local_changed:
            merged[key] = local_value
        else:
            merged[key] = disk_value
    return merged, conflicts
