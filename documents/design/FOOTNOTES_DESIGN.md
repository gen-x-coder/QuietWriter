# Voetnoten (1.7)

**Status:** gebouwd in 1.7.0-dev9, weergave herzien in dev10. **Besluit Lucas (16 oktober 2026):** `^[…]`, zo dicht mogelijk bij Markdown.

## Wat de schrijver ziet

Zoals in een tekstverwerker (dev10, na feedback van Lucas: "de cursor wordt klein maar verder zie ik niets"):

- **Ctrl+Alt+F** (zoals in Word) of **Toevoegen → Voetnoot**: in de tekst verschijnt een klein nummer in superscript, en onder aan het blad een korte streep met dat nummer en een knipperende cursor. Daar typ je de noot.
- **Enter**, **Esc** of nog eens **Ctrl+Alt+F** in de noot: terug naar de tekst, net na het nummer.
- **Klik op een nummer** in de tekst: die noot krijgt de cursor in de notenstrook.
- In de tekst is de noottekst ingeklapt. De cursor springt in één stap over een noot heen; **Backspace net na een nummer** (of Delete ervoor) haalt de hele noot weg, Ongedaan maken zet hem terug.
- Met een selectie maakt Ctrl+Alt+F (of rechtsklik → Opmaak → Voetnoot) van die tekst een voetnoot.
- Nummers tellen per hoofdstuk door en schuiven mee als je een noot ertussen zet. In het bestand staan geen nummers.
- De strook (`ui/footnote_strip.py`) is alleen weergave en invoer: elke letter gaat direct naar het `^[…]`-stuk in het manuscript. Ongedaan maken, opslaan en zoeken werken dus zoals altijd.

## Gekozen: Pandoc-inline-noot `^[tekst]`

```
Het huis stond aan de dijk.^[Volgens het kadaster gebouwd in **1902**.] Niemand wist…
```

| Optie | Voor | Tegen |
|---|---|---|
| **A. Inline `^[tekst]`** (gekozen) | Noot staat waar hij hoort; verplaats je de zin, dan gaat de noot mee. Geen labels of nummers. Gangbare Markdown (Pandoc), dus de Markdown-export blijft bruikbaar. Past in de bestaande inline-parser (één regel, net als vet). | Een noot is één alinea; een noot met meerdere alinea's kan niet. |
| B. Verwijzing `[^1]` + `[^1]: tekst` onderaan | Ook gangbaar | Nummers en labels bijhouden, noot ver van de plek, losse definities die wees kunnen raken. Technisch voor de schrijver. |
| C. Verborgen ID + aparte notenlijst (JSON) | — | Botst met de datawet "geen verborgen markers of ID's in het manuscript". |

## Regels

- `^[` opent, de eerste `]` zonder backslash sluit. Een noot in een noot bestaat niet. Binnen een noot werkt gewone opmaak (vet, cursief …).
- Getypte of geplakte `^` en `]` krijgen een onzichtbare backslash (`\^`, `\]`), net als `*`. Zo maakt typen nooit per ongeluk een noot en sluit een `]` in de noottekst hem niet te vroeg.
- Een losse `^[` zonder `]` blijft gewone tekst.
- **Zoeken, spelling en Meelezer** zien de noottekst (vanaf dev14 ook rode onderstreping in de notenstrook; het Spelling-paneel selecteert een fout in een noot in de strook en *Wijzigen* loopt via het notenveld); de Meelezer krijgt hem als `[Voetnoot: …]`. **Woordtelling** telt hem mee, als losse woorden.

## Exporteren

| Formaat | Resultaat |
|---|---|
| DOCX en Inzenden | Echte Word-voetnoten onder aan de pagina (`word/footnotes.xml`), door Word/LibreOffice genummerd. Gecontroleerd met LibreOffice. |
| EPUB | Nummer in de tekst met `epub:type="noteref"`; de noten onder aan het hoofdstuk (`epub:type="footnote"`), met een link terug. Nummering per hoofdstuk. Readers die het kennen, tonen een pop-up. |
| PDF | Nummer in de tekst, de noten onder aan het hoofdstuk (eindnoten per hoofdstuk). Echte paginavoetnoten horen bij de paperback-PDF (backlog #8). |
| Markdown | `^[…]` blijft staan; Pandoc begrijpt het. |
| DOCX-import | Word-voetnoten worden `^[…]` op dezelfde plek. |

## Geen nieuwe syntaxvlag

`book.json` krijgt geen nieuwe `manuscript_syntax`-feature. Een nieuwe vlag laat QuietWriter 1.6 en ouder het boek weigeren (fail-closed). Zonder vlag toont 1.6 een noot als gewone tekst `^[…]`; er gaat niets verloren. Klein nadeel: een in 1.7 getypte `^` of `]` toont in 1.6 een zichtbare backslash.

## Code

- `manuscript_syntax.py`: soort `footnote` in `_INLINE` en in `parse_inline_spans`; `^` en `]` escapebaar.
- `document_view.py`: `note_groups`, spaties rond noten in zichtbare tekst, `[Voetnoot: …]` voor de Meelezer.
- `docx_footnotes.py` (nieuw), `docx_io.py` (export en import), `exporting/markup.py` (`NoteCollector`), `pdf_exporter.py`, `epub_exporter.py`, `submission_exporter.py`.
- `ui/manuscript_editor.py` (`insert_footnote`, `footnote_spans`, cursorsprong, Backspace, nummers tekenen), `ui/footnote_strip.py` (notenstrook), `ui/presentation_highlighter.py` (inklappen), `ui/insert_panel.py`.
- Tests: `tests/current/test_footnotes_170.py`.
