# Dev.51 — Meelezer en Boekgeheugen

Deze iteratie verandert de herkenning en streamingweergave van expliciete geheugenvoorstellen.

- De parser accepteert varianten met hoofdletters/spaties in `[[QW_MEMORY|categorie]]`-blokken.
- Maximaal twee geldige voorstellen per antwoord worden als kaarten aangeboden; eventuele overige blokken blijven zichtbaar zodat er geen tekst stilzwijgend verdwijnt.
- Tijdens streaming worden gedeeltelijk ontvangen interne markers niet meer getoond.
- Opslag blijft uitsluitend na een expliciete klik op **Onthouden** plaatsvinden.
- De bestaande schijfverificatie van goedgekeurde herinneringen is ongewijzigd.

Getest met `python -m pytest tests/current/test_memory_proposals_dev51.py tests/current/test_meelezer_save_feedback_dev45.py tests/current/test_ai_architecture.py -q` (14 geslaagd).

Windows-acceptatietest: vraag aan de Meelezer expliciet om een nieuw vaststaand boekfeit voor te stellen; klik Onthouden, open Boekgeheugen, sluit het boek, open opnieuw en controleer of het feit in dezelfde sectie staat. Let op: als het model slechts in gewone taal suggereert iets te onthouden zonder geldig QW_MEMORY-blok, wordt er nog geen kaart aangeboden. Er is bewust geen automatische opslag van vrije modeltekst.
