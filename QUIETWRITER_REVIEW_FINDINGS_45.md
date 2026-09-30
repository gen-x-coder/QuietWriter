# QuietWriter: reviewronde 45 (versie 0.34.9: knop "Begrepen" bij de opt-in en testherstel)

**Gelezen:** de diff van `ai/ui.py`, met drie wijzigingen: een meldingsrij met de knop "Begrepen",
`_acknowledge_chapter_planning_notice` en een `contains`-controle die ook werkt zonder `contains`. Daarnaast
`REVIEW_NOTES_0349.md`. Buiten `ai/ui.py` en het versienummer is er geen productcode gewijzigd.

**Getest:** alle gevraagde suites met echte PySide6, plus runtime in de echte `MainWindow` met een nep-provider en
herstarts via hetzelfde ini-bestand.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Resultaat: groen

| Run | Resultaat |
|---|---|
| `pytest` | ✅ **219 geslaagd** |
| `pytest tests/current -k qt` | ✅ 14 geslaagd |
| `pytest tests/legacy -k qt` | ✅ 25 geslaagd; `test_ai_state_qt_runtime_0216` en `test_review_ai_scene_qt_0226` zijn weer groen |
| `pytest tests/legacy` | ✅ 449 geslaagd, 280 subtests; alleen de 2 fonttests falen |
| Koude start | ✅ |

### Runtime 0.34.9: 9/9

| # | Check | Resultaat |
|---|---|---|
| 1 | Schone instellingen → AI-context | ✅ checkbox uit, meldingsrij met "Begrepen" zichtbaar |
| 2 | "Begrepen" | ✅ melding weg, checkbox blijft uit, `ai_use_chapter_planning=False` opgeslagen, samenvatting "niet meegestuurd" |
| 3 | Herstart | ✅ melding blijft weg, checkbox blijft uit |
| 4 | Schone instellingen, checkbox direct aan | ✅ melding weg, `True` opgeslagen, de volledige hoofdstukplanning (inclusief de notitie van 6.000+ tekens) onder `PLANNING VAN HET HUIDIGE HOOFDSTUK` |
| 6 | Planning-context, hoofdstukwissel, Nieuw gesprek, Planning → Inhoud, Boekenplank | ✅ geen regressie; op de Boekenplank staan beide uit en de voorkeur blijft onaangetast |
| 7 | Nep-provider, schakelaar uit | ✅ geen automatische planning; de handmatige Planning-context gaat wel mee |
| — | Geen writes | ✅ `planning/` byte-identiek |

**Regressie:** de migratiematrix uit 0.34.8 (18/18), AI- en History-failsafe (7/7), hoofdstukcontext en railselectie
20/20, separator-regel, editorbron, publicatie, rondes 12–24, backend 47/15/8 ✅.

**Visueel** (`r45_notice.png`): "Begrepen" is een gewone secundaire knop, even zwaar als "Planning-context…" en "Context
bekijken", rechtsboven in de meldingsrij. Dat trekt niet te veel aandacht. Door de knop wordt de tekstkolom wel smaller,
waardoor de melding nu zes regels telt. Een kortere tekst zou helpen, bijvoorbeeld: "Nieuw: hoofdstukplanning kan mee met
AI-vragen. Staat uit. Bij een externe provider verlaat dit je computer." Dat is een keuze voor Lucas.

---

## Eén opmerking over `-k qt` (🟡, alleen tests)

`-k qt` selecteert alleen tests waarvan de **naam** "qt" bevat. In `tests/current` gebruiken nog **zeven bestanden** een
echt `MainWindow` of `QApplication` zonder "qt" in de naam. Die vallen dus buiten die run:

| Bestand | Bewaakt |
|---|---|
| `test_chapter_context_runtime_0340.py` | "In dit hoofdstuk" |
| `test_editor_source_text_0323.py` | de brontekst van de editor |
| `test_publication_dirty_0326.py` | de dirty-status van publicatieteksten |
| `test_rail_runtime_0330.py` | de rail en lage schermhoogtes |
| `test_review_0324.py` | notities en koude start |
| `test_review_export_correctness_0224.py` | de correctheid van de export |
| `test_settings_runtime_0322.py` | Instellingen en de preview |

Omdat ik de volledige suites altijd draai, gaat er bij mij niets verloren. Maar `-k qt` is als "de echte Qt-controle" dus
onvolledig.

**Robuuster:** laat `tests/conftest.py` elke test die de `app`-fixture gebruikt, of PySide6 importeert, automatisch markeren
met `@pytest.mark.qt`. Dan selecteert `pytest -m qt` precies alle echte Qt-tests, ongeacht de bestandsnaam. Zet ook in de
reviewnotes dat ik standaard de volledige `pytest` en `pytest tests/legacy` draai, en dat `-m qt` alleen de snelle
Qt-deelcontrole is.

## Conclusie

0.34.9 is groen en sluit de opt-in netjes af. "Begrepen" legt een bewuste keuze voor "uit" vast zonder omweg, blijft
bewaard na een herstart en raakt verder niets. Alle drie de testproblemen uit ronde 44 zijn opgelost, en beide
AI-regressietests in `legacy` draaien weer. Het enige punt is dat `-k qt` niet alle Qt-tests selecteert; een automatische
`qt`-marker lost dat op.

**Niet kunnen testen:** een echte AI-provider (nagebootst), echte Windows DPI-schaling en echte Dropbox-timing.
