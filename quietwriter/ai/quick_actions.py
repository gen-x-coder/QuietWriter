from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuickAction:
    key: str
    label: str
    prompt: str
    tooltip: str
    requires_selection: bool = False


QUICK_ACTIONS: tuple[QuickAction, ...] = (
    QuickAction(
        'feedback',
        'Feedback',
        'Geef concrete redactionele feedback op de meegegeven tekst. Benoem de belangrijkste sterke punten en verbeterpunten. Controleer relevante feiten, continuïteit en stijl tegen schrijverspersona, boekprofiel, boekgeheugen en geselecteerde Planning-context. Geef advies en aandachtspunten, maar schrijf of herschrijf geen manuscripttekst.',
        'Vul een prompt in voor gerichte redactionele feedback.',
    ),
    QuickAction(
        'persona_check',
        'Persona-check',
        'Controleer de meegegeven tekst tegen mijn schrijverspersona en boekprofiel. Benoem alleen concrete afwijkingen die er echt toe doen, met korte verbeteradviezen. Schrijf geen vervangende manuscripttekst.',
        'Vul een prompt in om stijl en stem tegen persona en boekprofiel te controleren.',
    ),
    QuickAction(
        'fact_check',
        'Feitencheck',
        'Controleer de meegegeven manuscripttekst op feitelijke continuïteit en tegenstrijdigheden met Boekgeheugen en geselecteerde Planning-context. Maak duidelijk onderscheid tussen actuele manuscripttekst, eerder vastgelegde feiten en geplande informatie. Benoem alleen concrete afwijkingen of onzekerheden.',
        'Vul een prompt in voor feiten- en continuïteitscontrole.',
    ),
)

QUICK_ACTION_BY_KEY = {action.key: action for action in QUICK_ACTIONS}
