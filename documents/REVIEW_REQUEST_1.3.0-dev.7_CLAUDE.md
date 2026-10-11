# QuietWriter 1.3.0-dev.7 — reviewopdracht voor Claude

Wijzig geen code. Review en test deze snapshot onafhankelijk.

## Context

Dev.7 verwerkt jouw review van dev.6. De beoogde wijzigingen zijn bewust beperkt tot:

1. B4: een al geopend privéboek mag niet open/bereikbaar blijven wanneer Presentatiemodus wordt ingeschakeld.
2. P1: persistente woordtellingcache per hoofdstuk op basis van pad + `mtime_ns` + bestandsgrootte.
3. P2: 200 ms debounce van het zoekveld.
4. De gebruikersnaam **Demo-modus** is gewijzigd in **Presentatiemodus** in alle vijf locales. De interne sleutel `bookshelf_demo_mode` blijft ongewijzigd.

`README.md` en een eventuele `README_EN.md` mogen niet worden aangepast. In deze snapshot was alleen `README.md` aanwezig en die is byte-identiek gebleven.

## Graag uitvoeren

### A. Volledige regressie

- volledige `pytest`-suite met PySide6;
- `--smoke-test`;
- locale-pariteit voor alle 5 talen;
- undefined-names / pyflakes zoals bij dev.6.

Rapporteer exacte aantallen.

### B. B4 / Presentatiemodus

Herhaal `demo136.py` en `demo136b.py` tegen dev.7 en controleer aanvullend:

- open een boek op een privéplank;
- wijzig tekst zodat er iets te bewaren is;
- zet Presentatiemodus aan;
- controleer dat de wijziging veilig is opgeslagen;
- controleer dat de huidige pagina de Boekenkast is;
- controleer dat `active_book`, editor, planning, profiel, geheugen, media/export en andere boekgebonden context het privéboek niet meer vasthouden;
- controleer dat terugnavigeren naar Schrijven/Planning het privéboek niet opnieuw toont;
- probeer een privéboek direct via `MainWindow.open_book()` te openen terwijl Presentatiemodus al aan staat: dat moet fail-closed worden geweigerd;
- publieke boeken moeten wel normaal open kunnen blijven/openen in Presentatiemodus;
- corrupt/future `library.json` moet ook voor `open_book()` fail-closed blijven.

Controleer daarnaast het foutpad: simuleer dat veilig opslaan/sluiten faalt. Dan moet Presentatiemodus weer **uit** gaan in plaats van “aan” te blijven terwijl privétekst zichtbaar is.

Er lijkt geen automatisch-heropen-pad voor het laatst geopende boek te bestaan in deze snapshot. Controleer dat nog één keer bij inspectie; als zo’n pad toch bestaat, test hem met Presentatiemodus al aan bij startup.

### C. Performance

Herhaal `shelfperf136.py` en `shelfperf136b.py` en rapporteer minstens:

- eerste opbouw;
- tweede `refresh()` zonder wijzigingen;
- Demo/Presentatiemodus aan/uit;
- sorteren;
- zoeken door `Boek 0` snel te typen;
- refresh na wijziging van precies één hoofdstuk;
- 25 boeken, en met het cachepad ook 100 en 500 boeken als praktisch.

Belangrijkste controles:

- een tweede refresh moet ongewijzigde hoofdstukken niet opnieuw parsen;
- na wijziging van één hoofdstuk moet alleen dat hoofdstuk opnieuw geteld worden;
- zoeken moet niet langer per toets een volledige dure refresh uitvoeren;
- geen stale woordtelling na normaal opslaan of een externe bestandswijziging waarbij `mtime_ns` of grootte verandert.

Geef aan of P3/P4 (covers/schaduwen) op Windows nu nog merkbaar genoeg zijn om vóór 1.3.0 aan te pakken. Niet op basis van theorie, maar op basis van waarneming/meting.

### D. Windows/visueel indien beschikbaar

- Presentatiemodus: aan/uit-label en checked-stijl;
- tooltip in de actieve taal;
- zoekveld voelt direct tijdens typen, resultaten volgen kort daarna;
- geen opvallende flits bij refresh;
- scrollen en hover met echte covers;
- 125% en 150% DPI als dat eenvoudig beschikbaar is.

## Reviewvraag

Classificeer bevindingen als:

- **blocker vóór dev.8 / 1.3.0**;
- **wel doen vóór 1.3.0**;
- **veilig backlog voor 1.4.x**.

Let vooral op privacy-correctheid, dataveiligheid en meetbare performance. Geen architectuurverbouwing voorstellen als de eenvoudige cache/debounce al voldoende is.
