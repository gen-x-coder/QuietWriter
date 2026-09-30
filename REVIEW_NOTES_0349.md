# Reviewnotities 0.34.9

## Verplicht door Claude met echte PySide6

Deze omgeving slaat een deel van de echte Qt-runtimechecks over. Draai daarom expliciet:

```
pytest tests/current -k qt
pytest tests/legacy -k qt
```

Draai daarnaast de normale suites:

```
pytest
pytest tests/legacy
```

De twee bekende fontresource-tests mogen als enige legacy-failures overblijven.

## Specifieke 0.34.9-checks

1. Schone instellingen: boek openen, AI-context openen. De hoofdstukplanningcheckbox staat uit en de nieuwe melding is zichtbaar.
2. Klik **Begrepen**. De melding verdwijnt, de checkbox blijft uit en `ai_use_chapter_planning=False` wordt opgeslagen.
3. Herstart met dezelfde instellingen: melding blijft weg, checkbox blijft uit.
4. Zet op een schone installatie de checkbox direct aan: melding verdwijnt en `True` wordt opgeslagen; de hoofdstukplanning gaat nog steeds exact zoals in 0.34.7/0.34.8 mee.
5. Legacy AI-runtimechecks `test_ai_state_qt_runtime_0216.py` en `test_review_ai_scene_qt_0226.py` moeten weer groen zijn.
6. Controleer dat `Planning-context…`, hoofdstukwissel, Nieuw gesprek, Planning → Inhoud en Boekenplank-state geen regressie hebben.
7. Nep-provider: met hoofdstukplanning uit gaat niets automatisch mee; handmatige Planning-context blijft onafhankelijk werken.

## Geen wijziging

Geen Planning-schemawijziging, geen contextafkapping, geen wijziging aan de promptsecties of de History/Integriteit-failsafes.
