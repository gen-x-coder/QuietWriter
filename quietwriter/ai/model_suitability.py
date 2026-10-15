"""Conservative model visibility for QuietWriter's manuscript chat.

This is not a quality ranking. General-purpose models remain visible even
when their descriptions mention coding. Only explicit coding families and
models without text output are excluded from the writing view.
"""
from __future__ import annotations
import re

_CODE_ID = re.compile(r'(?:^|[/._-])(?:coder|codex|codestral|devstral|code)(?=$|[/._:\-])', re.I)
_CODE_FAMILIES = ('bigcode/starcoder', 'poolside/', 'x-ai/grok-build-', 'cohere/north-mini-code')


def suitable_for_writing(model: dict) -> bool:
    """Return whether a model belongs in the simplified writing selection."""
    name = str(model.get('name') or model.get('id') or '').lower()
    if name == 'openrouter/free':
        return True
    if _CODE_ID.search(name.removesuffix(':batch')) or name.startswith(_CODE_FAMILIES):
        return False
    # Do not guess if the provider did not supply architecture metadata.
    # OpenRouter's architecture.output_modalities can distinguish image-only
    # and audio-only output from the text responses used by the Meelezer.
    output = model.get('output_modalities')
    if isinstance(output, (list, tuple)) and output and 'text' not in output:
        return False
    return True
