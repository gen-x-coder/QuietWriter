# Tussentijds rapport — QuietWriter 0.29.0

## Doel
De bestaande, uitvoerig geteste integriteitsbackend zichtbaar en bruikbaar maken zonder nieuwe automatische herstelmechanismen toe te voegen.

## Gebouwd
- Pagina **Integriteit & herstel** voor het actieve boek.
- Read-only audit met samenvatting van fouten en waarschuwingen.
- Detailweergave per probleem.
- Herstelknop alleen wanneer het probleem herstelbaar is én een geldige historische bron bestaat.
- Expliciete bevestiging vóór herstel.
- Na herstel automatische hercontrole.
- Expliciete migratie van een legacy boekformaat, inclusief bestaande pre-migration checkpoint.
- `BookBlockedError` voor bewust losgekoppelde/geblokkeerde boeken.

## Bewuste grenzen
- Geen 'herstel alles'-knop.
- `book.json` wordt niet via bestandsherstel teruggezet.
- Geen automatische reparatie bij het openen van een boek.
- Geen nieuwe planning/personagefuncties in deze release.
- Geen spelling-, autosave- of navigatieherontwerp; die volgen in 0.30/0.31.

## Runtimechecks voor Claude
1. Gezond boek: Integriteit meldt geen problemen en wijzigt geen enkel bestand.
2. Ontbrekend hoofdstuk met geldige History-kopie: probleem zichtbaar, herstelknop actief, na bevestiging byte-exact hersteld.
3. Hetzelfde zonder geldige History-kopie: herstelknop uit en geen wijziging.
4. Ongeldige planning JSON met geldige oudere object-kopie: herstel werkt en maakt `pre_integrity_repair`.
5. Gemodificeerde media met juiste historische SHA-kopie: alleen geldige bron wordt aangeboden/gebruikt.
6. Externe wijziging tussen audit en herstel: herstel wordt geweigerd en live boek blijft onaangeraakt.
7. Permanente schrijflock tijdens herstel: foutmelding, geen vals succes, huidige bytes blijven veilig.
8. Geblokkeerd boek: `BookBlockedError` wordt als geblokkeerde toestand benoemd.
9. Legacy boek: migratieknop alleen zichtbaar indien nodig; migratie maakt checkpoint en pagina hercontroleert daarna.
10. Navigatie naar Integriteit vanuit dirty Editor/Planning/Boekdetails respecteert de bestaande saveguards.
11. Future-format boek kan niet via deze pagina worden 'gerepareerd' of gedowngraded.
12. Controleer hashes van de volledige boekmap vóór/na een read-only audit: identiek.

## Testomgeving ChatGPT
PySide6-runtimetests kunnen in deze omgeving nog steeds worden overgeslagen. Backendtests en bronintegratie worden lokaal uitgevoerd; Claude kan de echte Qt-flow headless nalopen.

## Lokale teststand
- 509 tests geslaagd, 27 Qt-tests overgeslagen, 280 subtests geslaagd.
- Alleen de 2 bekende fontresource-tests falen door het ontbrekende `resources/fonts/font_manifest.json`.
- Gerichte 0.29/integriteit/storage-tests: 19 geslaagd.
