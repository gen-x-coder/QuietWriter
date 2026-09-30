# QuietWriter: reviewronde 35 (versie 0.33.1, de afsluitende correctiebuild van 0.33)

**Gelezen:**
- de diff van `main_window.py`: `program_host` vast onderaan, `_register_nav_separator` en de logica voor de
  separators in `_render_rail`;
- de drie uitlegteksten;
- de testfixes;
- `REVIEW_NOTES_0331.md` en `TECHNISCH_ONTWERP_0340.md`.

**Getest:** runtime in de echte `MainWindow` met het echte stylesheet. Alle 16 toestanden heb ik opnieuw doorgelopen,
elk in een vers gebouwd venster. Daarbij heb ik de volgorde van koppen, items en separators vergeleken met mijn eigen
verwachtingsregel.

Legenda: 🔴 bevestigd/gereproduceerd · 🟡 bevestigd, beperkte impact

## Resultaat: groen

| # | Check (REVIEW_NOTES_0331) | Resultaat |
|---|---|---|
| 1 | Volledige suite met PySide6 | ✅ **622 geslaagd**, 280 subtests. Alleen de 2 fonttests falen; beide railtests uit ronde 34 zijn nu groen |
| 2 | 700, 720 en 768 px, rail uitgeklapt | ✅ Menu vast bovenaan (y=10); PROGRAMMA staat buiten het scrollgebied; Prullenbak volledig in beeld zonder scrollen (onderkant op 667, 687 en 735 px); alleen het middendeel scrollt |
| 3 | Rail ingeklapt, 16 toestanden | ✅ geen koppen; precies één separator minder dan het aantal zichtbare groepen; nooit een separator aan het begin, aan het eind of twee achter elkaar; geen separator voor een verborgen groep |
| 3 | Rail uitgeklapt | ✅ nergens een separator; de koppen nemen het over |
| 4 | Preview en commit van AI uit en Geavanceerd uit | ✅ alle checks uit ronde 34 opnieuw groen (terugkeerdoel, AI-paneel met invoer, Planning- en Boekenplank-routes, in- en uitklappen tijdens de preview) |
| 5 | Scrollbalk met het echte stylesheet | ✅ 5 px, geen horizontale balk, geen afgekapte labels (viewport 203 px uitgeklapt, 49 px ingeklapt) |
| 6 | Teksten | ✅ alle drie zeggen "bij iedere AI-vraag … naar de gekozen AI-provider; bij een externe provider verlaten deze gegevens je computer". Het Boekprofiel noemt de voorrangsregel, en de Persona verwijst er ook naar. Dit klopt met `ai/prompting.py` en `ai/context.py` |
| 7 | Railmatrix uit 0.33.0 (A–D) | ✅ 26/26. De ene FAIL in mijn script is de oude controle "Prullenbak na scrollen in beeld": hij zit nu bewust niet meer in het scrollgebied |
| 7 | Smoke-regressie 0.32 | ✅ editorbron 8/8, notities 5/5 plus 4× niets geschreven, publicatie 18/18, scène/afbeelding 4× behouden, rondes 12–24 op de basislijn, randgeval ronde 24, herkomst, backend 47/15/8 |

---

## Twee kleine punten (🟡, geen blokkade om 0.33 te sluiten)

### 1. De actieve pagina scrolt niet in beeld

Ga je naar een pagina via code en niet via een klik, dan krijgt de knop wel de actieve markering, maar hij blijft onder
de vouw staan. Dat gebeurt bij `show_book_profile()`, bij een redirect na Opslaan, en straks bij links vanuit
"In dit hoofdstuk" of het AI-paneel.

Runtime op 1280×700: na `show_book_profile()` is `isChecked=True`, maar de knop staat niet in de viewport en de scrollpositie
is 0.

**Fix:** één regel in `_sync_nav_selection`:
`self.rail_scroll.ensureWidgetVisible(active_button)` (alleen als die knop in het scrollgebied zit).

### 2. Op gewone laptophoogtes staat AI-CONTEXT standaard onder de vouw

Het vastzetten van PROGRAMMA is een goede keuze, maar het middendeel wordt daardoor klein. Gemeten met een open boek,
AI aan, Geavanceerd aan, rail uitgeklapt, scrollpositie 0:

| Venster | Viewport middendeel | Direct zichtbaar | Niet zichtbaar |
|---|---|---|---|
| 1280×700 | 422 px | Boekenplank … Integriteit | Boekgeheugen, Boekprofiel |
| 1280×720 | 442 px | Boekenplank … Integriteit | Boekgeheugen, Boekprofiel |
| 1366×768 | 490 px | Boekenplank … Integriteit | Boekgeheugen half, Boekprofiel niet (zie `r35_h768.png`) |
| 1440×900 | 622 px | alles | — |

1366×768 is nog steeds een veelvoorkomende laptopresolutie, en na de taakbalk blijft daar ongeveer 720 px over. Precies
de nieuwe groep AI-CONTEXT is daar dus standaard onzichtbaar. De enige hint is een scrollbalk van 5 px.

Dit is een ontwerpkeuze voor jou, niet voor mij. Twee lichte opties:
- **Compacte knoppen wanneer het middendeel niet past:** 40 in plaats van 48 px, alleen als de viewport te laag is. Bij
  768 past dan alles.
- **Een subtiele vervaging onderaan het scrollgebied** zolang er meer inhoud is. Dat is gangbaar in desktop-UI's en kost
  geen hoogte.

---

## Feedback op TECHNISCH_ONTWERP_0340 (ideeën, niet meteen inbouwen)

Het ontwerp is goed afgebakend: alleen-lezen, geen nieuwe bron van waarheid, geen automatische herkenning, en AI-context
pas later en expliciet. Leg deze randgevallen vooraf vast in het ontwerp, want dat zijn de plekken waar eerdere rondes
fouten vonden:

1. **Welke Planning-stand toont het blok?** Stel dat er in Planning onopgeslagen wijzigingen zijn in personages of scènes.
   Toont het blok dan de opgeslagen stand (`PlanningStore`) of de lokale stand? Mijn advies: de opgeslagen stand, en
   verversen na een geslaagde Planning-save en na een centrale adopt.
2. **Geen hoofdstuk actief:** het blok verbergt zich of toont een rustige lege staat bij Voorwoord/Nawoord en andere
   publicatie-items, bij het voorbeeld uit de geschiedenis (een alleen-lezen archief) en bij een beschadigd hoofdstuk
   (`_chapter_corrupt`).
3. **Verweesde koppelingen:** een scène kan wijzen naar een verwijderd of gesplitst hoofdstuk, of naar een verwijderd
   personage. Het blok moet dat stil overslaan, zonder exceptie.
4. **`characters.json` of `outline` beschadigd:** het blok toont een korte melding en de editor blijft volledig werken. Dat
   zegt het ontwerp al. Neem het ook op in de testlijst voor de corrupte-bronmatrix.
5. **AI uit:** het blok blijft gewoon zichtbaar. Het is Planning, geen AI. Neem het mee in het railmodel of de
   feature-matrix, zodat dit ook bij de volgende zichtbaarheidswijziging getest wordt.
6. **Plek en hoogte:** het linkerpaneel (Inhoud) is al vol, en rechts zijn er panelen voor Zoeken, AI en Spelling. Een
   inklapbaar blok onder de hoofdstukboom concurreert om dezelfde hoogte als hierboven. Besluit bewust waar het staat en
   test het op 720 px. Mijn voorkeur: een eigen rechterpaneel ("In dit hoofdstuk") naast Zoeken, AI en Spelling. Dat
   hergebruikt bestaand paneelgedrag en kost geen hoogte in de hoofdstukboom.
7. **"Acties leiden naar Planning":** gebruik daarvoor de centrale navigatie (`show_planning` + selecteren) en zorg dat
   Planning dan ook in beeld scrolt (punt 1 hierboven).

---

## Samenvatting

| # | Bevinding | Status | Impact |
|---|---|---|---|
| — | PROGRAMMA vast onderaan, separators in de ingeklapte rail, teksten, testfixes, matrix, preview/commit en regressie | ✅ | — |
| 1 | De actieve railknop scrolt niet in beeld bij navigatie via code | 🟡 | Klein; wordt belangrijker met 0.34-links |
| 2 | AI-CONTEXT staat op 700–768 px standaard onder de vouw | 🟡 | Ontwerpkeuze; vindbaarheid op laptops |

**Conclusie:** 0.33.1 is groen. Wat mij betreft kan 0.33 dicht. Punt 1 kan als eenregelige fix in de eerste 0.34-build mee,
punt 2 is een keuze voor Lucas. Het 0.34-ontwerp is een goede eerste slice; leg de zeven randgevallen hierboven vóór de
bouw vast.

**Niet kunnen testen:**
- een echt scherm met DPI-schaling (125% of 150% op Windows maakt het hoogteprobleem van punt 2 groter);
- de ophaalroute van AI-modellen;
- echte Dropbox-timing.
