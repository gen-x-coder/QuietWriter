"""Export purposes for guided export.

A purpose is what the writer wants to do ("read on an e-reader"); it maps to
one existing export format plus a few defaults. Ids are stable and never
translated. The UI owns all visible text.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

STEP_PURPOSE = 'purpose'
STEP_CHECK = 'check'
STEP_CONTENT = 'content'
STEP_APPEARANCE = 'appearance'
STEP_EXPORT = 'export'


@dataclass(frozen=True)
class ExportPurpose:
    id: str
    format: str
    has_appearance: bool
    defaults: dict = field(default_factory=dict)


PURPOSES: tuple[ExportPurpose, ...] = (
    ExportPurpose('ereader', 'epub', True),
    ExportPurpose('print', 'pdf', True),
    ExportPurpose('word', 'docx', False),
    ExportPurpose('share', 'qwbook', False, {'qwbook': {'include_history': False, 'include_ai_chat': False}}),
    ExportPurpose('backup', 'qwbook', False, {'qwbook': {'include_history': True, 'include_ai_chat': True}}),
    ExportPurpose('website', 'markdown', False),
)

PURPOSES_BY_ID = {purpose.id: purpose for purpose in PURPOSES}


def get_purpose(purpose_id: str | None) -> ExportPurpose | None:
    return PURPOSES_BY_ID.get(str(purpose_id or ''))


def steps_for(purpose_id: str | None) -> tuple[str, ...]:
    purpose = get_purpose(purpose_id)
    if purpose is not None and purpose.has_appearance:
        return (STEP_PURPOSE, STEP_CHECK, STEP_CONTENT, STEP_APPEARANCE, STEP_EXPORT)
    if purpose is None:
        # Before a choice the most common (5-step) route is shown.
        return (STEP_PURPOSE, STEP_CHECK, STEP_CONTENT, STEP_APPEARANCE, STEP_EXPORT)
    return (STEP_PURPOSE, STEP_CHECK, STEP_CONTENT, STEP_EXPORT)


def apply_purpose(saved: dict, purpose_id: str) -> dict:
    """Return a draft: saved settings + format + purpose defaults.

    Only keys present in the purpose defaults are overwritten, so an earlier
    template/paper choice survives. The input is never mutated.
    """
    purpose = get_purpose(purpose_id)
    if purpose is None:
        raise ValueError(f'Onbekend exportdoel: {purpose_id}')
    draft = copy.deepcopy(saved or {})
    draft['format'] = purpose.format
    draft['purpose'] = purpose.id
    for group, values in purpose.defaults.items():
        merged = dict(draft.get(group) or {})
        merged.update(values)
        draft[group] = merged
    return draft
