# Review 0.34.10

Doel: 0.34 afronden zonder nieuwe productlogica.

## Verplicht door Claude met echte PySide6

Voer vanaf de projectroot uit:

```bash
pytest
pytest -m qt
pytest tests/legacy
pytest tests/legacy -m qt
python main.py
```

Belangrijk: gebruik `-m qt`, niet `-k qt`. `tests/conftest.py` markeert tijdens collectie automatisch tests die de `app`-fixture gebruiken of PySide6 importeren. Controleer dat de eerder gemiste Qt-bestanden (rail, Instellingen, In dit hoofdstuk, editorbron/publicatie en export-runtime) in de `-m qt`-selectie terechtkomen.

## Productcheck

1. Nieuwe gebruiker: open AI → Context. De opt-inmelding moet compacter zijn en nog steeds expliciet zeggen dat hoofdstukplanning standaard uit staat en bij een externe provider de computer verlaat.
2. **Begrepen**: melding weg, checkbox uit, keuze blijft na herstart.
3. Checkbox aan: bestaand 0.34.7–0.34.9 gedrag blijft gelijk; hoofdstukplanning gaat alleen dan mee.
4. Geen wijziging aan Planning-bestanden of promptsecties buiten de bestaande 0.34.9-contracten.

Als alle runs groen zijn, kan 0.34 functioneel worden gesloten.
