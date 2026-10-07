# QuietWriter 1.2.14 — Centrale manuscriptinterpretatie

## Kern

Deze versie legt de eerste technische basis voor één consistente interpretatie van manuscripttekst. De opslag blijft gewone, leesbare tekst met Markdownconventies; bestaande boeken worden niet gemigreerd of herschreven.

## Gewijzigd

- Nieuwe read-only `DocumentView` als centrale interpretatielaag voor manuscriptblocks, inline spans en bronranges.
- Editor, XHTML/EPUB, PDF en DOCX-export gebruiken dezelfde blockclassificatie.
- De presentatie-highlighter gebruikt dezelfde block- en inlineinterpretatie.
- Woordtelling gebruikt de semantische documentlaag en telt structurele markup zoals scènebreuken en lijstprefixen niet meer als woorden.
- `MANUSCRIPT_SYNTAX.md` toegevoegd: huidige 1.2.x-regels zijn nu expliciet vastgelegd.
- Inline opmaak wordt per fysieke manuscriptregel geïnterpreteerd en koppelt dus niet meer onbedoeld over alinea's heen in de nieuwe documentlaag.
- Letterlijke, ongepaarde tekens zoals `*31623455` blijven gewone tekst.
- Bekende dubbelzinnigheden zoals `- Kom je?` en `1944. ...` worden nog niet stil aangepast; een toekomstige escapingstrategie wordt apart ontworpen.
- Oude ongebruikte `exporting/xhtml.py` verwijderd zodat er minder concurrerende parsers bestaan.
- Verouderde roadmap-/releasetests aangepast aan de opgeschoonde documentatiestructuur.

## Niet gewijzigd

- Geen nieuw opslagformaat.
- Geen automatische migratie van bestaande manuscripten.
- Geen nieuwe QWM-v2-syntax.
- Geen wijziging aan DOCX-import in deze stap.
- Geen wijziging aan de publieke release-/signingstrategie.

## Testen

De volledige geautomatiseerde testsuite moet groen zijn voordat deze ontwikkelversie als nieuwe baseline wordt gebruikt.
