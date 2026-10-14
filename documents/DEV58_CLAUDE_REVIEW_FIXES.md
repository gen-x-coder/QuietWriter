# QuietWriter 1.5.0-dev.58 — eerste correctieronde Claude-review

Gebaseerd op de onafhankelijke review van dev.57 (14 oktober 2026). Dit is een beperkte hardening-iteratie en **geen** afgetekende release.

## Wijzigingen

- H1: smoke-context maakt nu zijn werkmap aan; de startup-gate start voortaan `main.py --smoke-test`, niet alleen de importeerbare `quietwriter.app` module.
- H2: meerregelige voorstellen worden als één doorlopende geheugenentry opgeslagen. Duplicaatdetectie en terugleescontrole krijgen dezelfde genormaliseerde tekst.
- H3: AI-chat en gespreksarchief openen nooit meer links automatisch. Alleen HTTPS-links komen na expliciete bevestiging in de browser terecht; `file:`, `http:`, lokale applicaties en andere schema's worden geweigerd. De Markdown-renderer verwerkt geen ruwe HTML meer.
- M1: de tekst op de geheugenvoorstelkaart wordt letterlijk getoond (PlainText), zodat verborgen HTML geen onzichtbare inhoud bij de goedkeuring kan toevoegen.
- M4: handmatig Onthouden schrijft een nieuwe entry op basis van de op schijf gelezen versie. Niet-opgeslagen bewerkingen op de Boekgeheugen-pagina worden niet meer ongevraagd meegenomen.
- M3 (gedeeltelijk): de guard knipt tekst van het AI-model niet langer weg; herkenbare onterechte geheugenclaims krijgen een corrigerende toelichting. Een beperkte herkenning van citaten voorkomt dat een geciteerd personage ten onrechte wordt gecorrigeerd. Meertalige volledigheid staat nog open.
- L3: alle complete interne geheugenmarkeringen worden uit zichtbare AI-tekst verwijderd; maximaal twee geldige voorstellen worden getoond.

## Getest

- Python compileall op de broncode geslaagd.
- 21 gerichte tests rond geheugen en de rol van de Meelezer geslaagd.
- Pure-Python smokecontrole van dubbele en meerregelige geheugenentries geslaagd.

**Niet in deze omgeving getest:** Qt-UI, echte Windows-start en volledige smoke-test. PySide6 is hier niet geïnstalleerd. Test de echte start vóór GitHub-commit en release; de upstream review heeft aangetoond dat eerdere versies bij de smoke-test konden vastlopen.

## Nog open uit Claude-review

- M2: manuscriptcontext als onbetrouwbare data afbakenen (bij voorkeur apart bericht), plus neutralisatie van interne geheugenmarkers in geciteerde context.
- M3: de response-guard verfijnen en meertalige opslagclaims vollediger afdekken.
- M5: zeven ontbrekende vertalingen in OpenRouter-browserlogin en Qt-meldingen.
- M6/L1/L2: cancellation vóór headers, onderbroken SSE-stream en parserrobustheid.
- L4/L5: pop-out bij terug naar boekenkast, API-sleutelopslag, endpointvalidatie, contextvenster, synchroon modellen ophalen, migratie oude verbindingsmethode.
- Vijf verouderde versie-/semantische tests, CHANGELOG-hiaten en de volledige test-suite.

Niet automatisch al deze wijzigingen tegelijk doorvoeren: eerst de hardening-basis op Windows valideren en dan de volgende cluster verwerken.
