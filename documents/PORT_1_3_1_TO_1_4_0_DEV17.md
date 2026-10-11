# Overname 1.3.1-hotfix in 1.4.0-dev.17

De overdracht is semantisch verwerkt op basis van `QUIETWRITER_1.3.1_TO_1.4_PATCH_HANDOFF.md`.

- `spell_engine.py`: tijdsbudget rond de `spylls` edit-kandidatengenerator.
- `dictionary_catalog.py`: behoud van meerdere bronnen per taal met veilige fallback.
- `settings_page.py`: aparte woordenboekbronkeuze, opslag en herstel van de keuze; de 1.4-back-uppagina is behouden.
- `editor_page.py`: respecteert opgeslagen woordenboekbron.
- Vijf talen: alleen de vijf relevante keys overgenomen; bestaande 1.4-strings behouden.
- Beide hotfix-regressietests toegevoegd.

De volgende grotere verbetering is asynchrone spellingvoorstellen. Dit is **niet** inbegrepen in dev.17; het 1-secondebudget beperkt werk, maar sluit een korte blokkering van de GUI nog niet volledig uit.
