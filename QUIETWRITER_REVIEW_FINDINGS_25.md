# QuietWriter: reviewronde 25 (versie 0.31.6, dirty bron wordt extern onleesbaar)

**Gelezen:**
- de diffs van `main_window.py` (preflight voor notities);
- `book_memory_page.py` en `book_profile_page.py`: modus `corrupt` in `prepare_adoption`, en een vroege uitweg in
  `_resolve_external_change`;
- `planning_page.py` en `notes_page.py`;
- `REVIEW_NOTES_0316.md`.

**Getest:** runtime in de echte `MainWindow` (PySide6, headless). Na elke adopt heb ik de objectidentiteit van alle negen
boekreferenties gecontroleerd, en ook de bytes van het beschadigde bestand.

## Resultaat: groen

**Testsuite:** 579 geslaagd, 280 subtests, 0 overgeslagen. Alleen de 2 bekende fonttests falen.

### Het randgeval uit ronde 24 (exacte reproductie)

| Keuze in de oude dialoog | 0.31.5 | 0.31.6 |
|---|---|---|
| "Versie op schijf" | vast: navigeren, Integriteit en sluiten geweigerd | ✅ naar Schrijven, Integriteit bereikbaar, sluiten werkt, lokale tekst in History, bytes intact |
| "Mijn boekgeheugen" | vast, lokale tekst **niet** in History | ✅ idem; er verschijnt geen keuzedialoog meer |
| Geen keuze | vast | ✅ idem |

### A–C: Boekgeheugen, Boekprofiel en Planning-notities, elk langs twee routes

Getest langs twee routes: **direct** (save of navigatie vanaf de pagina) en **onverwant** (een extern hoofdstuk gewijzigd,
daarna een centrale adopt).

| Check | memory direct | memory onverwant | profile direct | profile onverwant | notes direct | notes onverwant |
|---|---|---|---|---|---|---|
| Lokale tekst in `conflict_local` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Live corrupte bytes byte-identiek | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Alle negen referenties op hetzelfde nieuwe `Book` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pagina alleen-lezen met foutmelding, niet dirty | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Geen keuzedialoog "Mijn versie / Versie op schijf"; wel de melding "…veilig bewaard" | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Notities: de lokale tekst wordt niet teruggezet over de foutstaat; de timer (3 s gewacht) veroorzaakt geen lus | — | — | — | — | ✅ | ✅ |
| Integriteit bereikbaar, herstel actief | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Na herstel bewerkbaar en opslaanbaar | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sluiten werkt | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### D: failure-injection (het herstelpunt zelf faalt)

| Pagina | Resultaat |
|---|---|
| Boekgeheugen | ✅ niets omgebonden, `_active_book` oud, lokale tekst zichtbaar en dirty, bytes intact, melding "Conflict niet opgelost" |
| Boekprofiel | ✅ idem |
| Planning-notities | ✅ idem |

De garantie uit 0.31.5 blijft dus staan.

### Regressie: alles groen

| Reeks | Resultaat |
|---|---|
| Ronde 24 (adopt failure-injection en succespad) | 10/10 |
| Ronde 23 | 12/12 |
| Ronde 22 | 12/12 |
| Spelling | 6/6 |
| Ronde 21 | 9/9 |
| 0.31.0 | 18/18 |
| Corruptie rondes 16–18 | 2/2, 5/5, 3/3 |
| Integriteit | 19/19 |
| Rondes 11–13 | 36/36, 32/32, 10/10 |
| Backend 9–11 | 47/47, 15/15, 8/8 |
| Openen met corrupte bronnen | geen crash, geen gemengde toestand |

---

## Een observatie over herstel (geen bug, wel goed om bewust te kiezen)

Na dit scenario zet **Integriteit de lokale concepttekst terug**, niet de laatste versie die vóór de beschadiging op schijf
stond. Dat komt doordat `latest_recovery_file` de **nieuwste geldige** kopie in History kiest, en dat is de zojuist
gemaakte `conflict_local`-snapshot met de lokale invoer. Alleen `pre_integrity_repair` wordt overgeslagen.

In mijn test: schijf "GOED GEHEUGEN" → lokaal "LOKAAL MEMORY" (dirty) → schijf raakt beschadigd → herstel → Boekgeheugen
toont **"LOKAAL MEMORY"**. Voor notities gebeurt hetzelfde.

Voor dit geval is dat waarschijnlijk precies wat een schrijver wil: de andere kant was onleesbaar, dus er is geen geldige
externe tekst die "wint". In het algemeen kan een `conflict_local`-snapshot echter invoer bevatten die bij een gewoon conflict
bewust **niet** live is gezet ("Versie op schijf gekozen"). Een latere Integriteit-reparatie zou die dan alsnog live
terugzetten. Twee lichte opties:
- de herkomst tonen in het detailpaneel van Integriteit ("Herstelkopie: lokale conflictversie van 21:34"), zodat de
  gebruiker weet wat er terugkomt;
- of `conflict_local` alleen gebruiken als er geen nieuwere `manual`, `daily` of `pre_*`-kopie is.

Ik zou het eerste doen. Het is transparant en verandert geen gedrag.

## Conclusie

0.31.6 sluit het laatste randgeval. Een onleesbare eigen bron blokkeert de app niet meer, lokale invoer staat altijd eerst in
History, de beschadigde bytes blijven onaangeroerd, en als het herstelpunt zelf faalt, blijft alles op het oude boek staan.
Er staan geen bekende open punten meer op de lijst.

**Niet kunnen testen:** echte Windows- en Dropbox-locks (nagebootst) en de visuele weergave van de meldingen.
