# Review Notes 0.35.4

Doel: 0.35 afsluiten zonder nieuwe features.

## Verplicht met echte PySide6 / Python 3.12
- `pytest`
- `pytest -m qt`
- `pytest tests/legacy`
- `pytest tests/legacy -m qt`
- `python main.py` koude start
- `python tools/check_undefined_names.py`

## Planning regressie — echte UI-route
Controleer in NL én EN:
1. kies een bekende scènestatus en sla op → canonieke Nederlandse opslagwaarde;
2. open een scène met custom status `in revisie`, wijzig alleen synopsis, sla op → status blijft exact `in revisie`;
3. kies `uitgewerkt`, typ daarna zonder Enter `eerste versie`, sla op → `eerste versie`;
4. typ in Engels exact een bekend label zoals `written` → opslag `geschreven`;
5. kies een relatietype, typ daarna custom `buurman van` / `neighbor of`, voeg toe → custom tekst blijft exact staan en er wordt geen verkeerde inverse relatie gemaakt.

## CI gate
`python tools/check_undefined_names.py` moet groen zijn ondanks bestaande ongebruikte imports. Introduceer tijdelijk één undefined name in een kopie en bevestig dat de checker dan rood wordt.

## Pythoncontract
QuietWriter ondersteunt bron/runtime vanaf Python 3.12. Controleer koude start onder 3.12. Optioneel: start `main.py` onder 3.11 en controleer dat de versiecontrole vóór import een nette melding/exitcode 2 geeft.
