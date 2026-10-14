"""Guard against AI-generated claims about local book-memory writes.

Only the application can confirm persistence. This guard deliberately rewrites
narrow first-person completion claims, leaving other prose intact.
"""
from __future__ import annotations

import re

_STORAGE_CLAIM = re.compile(
    r'(?i)(?<!\w)(?:ik\s+heb\s+(?:dit|deze\s+informatie|het\s+feit|deze\s+kennis|dat|het)?\s*'
    r'(?:al\s+)?(?:opgeslagen|vastgelegd|genoteerd|toegevoegd|bewaard|onthouden)\b'
    r'|ik\s+(?:noteer|sla|bewaar|onthoud|registreer|voeg)\b'
    r'[^.!?\n]{0,130}\b(?:boekgeheugen|geheugen|voor\s+dit\s+boek)\b)'
    r'[^.!?\n]*(?:[.!?]|(?=\n|$))'
)

_NOTICE = 'Ik kan dit niet zelf opslaan. Gebruik **Onthouden** in QuietWriter om het feit aan het Boekgeheugen toe te voegen.'


def guard_memory_claims(answer: str) -> str:
    """Flag likely storage claims without altering model text or quoted fiction."""
    source = answer or ''
    if source.strip().lower().startswith('quietwriter bevestigt:'):
        return source
    quote_pattern = re.compile(r'"[^"\n]*"|“[^”\n]*”|„[^”"\n]*[”"]|‘[^’\n]*’|(?<!\w)\'[^\'\n]*\'')
    quote_spans = [(m.start(), m.end()) for m in quote_pattern.finditer(source)]
    extra_claims = re.compile(
        r'(?i)(?:\b(?:genoteerd|opgeslagen in (?:het |je )?boekgeheugen)\s*[!.]|'
        r"\b(?:i(?:'ve| have) (?:saved|stored|noted|remembered)|"
        r'ich habe (?:das|es|dies) (?:gespeichert|notiert)|'
        r"j['’]ai (?:enregistré|noté)|he (?:guardado|anotado))\b[^\n.!?]*[.!?]?)"
    )
    for match in list(_STORAGE_CLAIM.finditer(source)) + list(extra_claims.finditer(source)):
        if any(start <= match.start() < end for start, end in quote_spans):
            continue
        line = source[source.rfind('\n', 0, match.start()) + 1:match.start()]
        if line.lstrip().startswith('>'):
            continue
        if _NOTICE in source:
            return source
        return source.rstrip() + '\n\n' + _NOTICE
    return source
