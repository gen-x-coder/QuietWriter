# Rustige grafiek van de afgelopen 30 dagen — voorstel

**Status:** gebouwd in 1.7.0-dev13. **Besluit Lucas (16 oktober 2026):** "Grafiek van 30 dagen is goed. Het past binnen de design principes." Code: `ui/progress_strip.py`, `WritingProgressStore.recent_days`, `ui/book_details.py` (`_refresh_progress_strip`, ook bij elke keer tonen).

## Wat er al is
- Opt-in *Vandaag geschreven bijhouden* (Instellingen → Algemeen, standaard uit), zie `SCHRIJFDOELEN_DESIGN.md`.
- `writing_progress.py` bewaart per boek per dag de **positieve groei** bij opslaan, lokaal buiten de werkmap, **60 dagen**. Schrappen telt niet af.
- De gegevens voor een grafiek liggen er dus al. Er hoeft niets aan opslag of formaat te veranderen.

## Voorstel
Eén regel extra in **Boekdetails → Schrijfdoel**, onder *Voortgang*: **Laatste 30 dagen**.

- 30 smalle staafjes, één per dag, oudste links, vandaag rechts. Een dag zonder schrijven is een dun grijs streepje (geen gat, geen rood).
- Geen getallen op een as, geen gemiddelde, geen doellijn, geen reeks ("streak"), geen vergelijking met vorige maand, geen felicitatie.
- Eén neutrale regel eronder: *9.890 woorden op 14 van de 30 dagen · alleen op deze computer*.
- Muis op een staafje: *di 14 okt · 812 woorden*. Met het toetsenbord is de regel eronder genoeg (de staafjes zijn geen bediening).
- Kleur: de accentkleur van het thema, vandaag iets voller. Werkt in alle thema's.
- ~~Alleen zichtbaar als bijhouden aan staat en er iets geteld is.~~ **dev14, na Windows-test Lucas** (hij zag de grafiek niet en wist niet waarom): de regel staat er altijd. Uit: een zin die naar Instellingen verwijst. Aan maar leeg: alleen grijze streepjes en *Nog geen woorden geteld…*.

Proefbeeld (offscreen, met verzonnen gegevens): meegestuurd in de chat bij dev12.

## Bewust niet
- Niet in de editor, niet op de Boekenkast, niet in een eigen pagina of dashboard (productregels 1 en 2, "Rust boven feature density").
- Geen totaal over alle boeken heen (de telling is per boek; een totaal zou een nieuwe plek nodig hebben).
- Geen dagdoel.

## Twijfelpunten voor Lucas
1. **Past het?** Het voordeel is een eerlijk beeld van je ritme zonder druk. Het risico is dat een rij grijze streepjes toch voelt als "achter". De stille regel eronder telt alleen wat er wél was.
2. **Plek:** Boekdetails is rustig, maar ver weg tijdens het schrijven. Dat vind ik juist goed; een plek dichter bij de tekst zou het een motivatie-instrument maken.
3. **Twee computers:** de telling blijft per computer. De regel zegt dat, zodat niemand denkt dat er woorden "kwijt" zijn.

## Omvang als Lucas ja zegt
Klein: één widget (±100 regels) in `ui/book_details.py` of een eigen `ui/progress_strip.py`, een leesfunctie `WritingProgressStore.days(book_id, 30)`, vier vertaalsleutels, tests (lege periode, uit, alleen vandaag, 60-dagengrens).
