# Reviewopdracht QuietWriter 1.3.0-dev.12

Wijzig geen code. Review deze snapshot als opvolger van dev.11.

## Context
Lucas heeft dev.11 op Windows getest. Alle functionele schrijfdoeltests zijn geslaagd. Dev.12 bevat alleen UI/UX-polish in Boekdetails en de bijbehorende versie-/testmetadata.

## Controleer
1. Volledige pytest-suite met PySide6, smoke-test, locales, undefined-names en pyflakes.
2. Regressie van alle dev.11-schrijfdoeltests: opt-in, save-delta, pauzeren/hervatten, doel/deadline, Boekenkast en versieherstel.
3. Boekdetails visueel/structureel: Schrijfdoel en Boekomslag gebruiken hetzelfde tweekolomspatroon als Instellingen, met titel/uitleg links en bediening rechts.
4. Einddatum: zonder opgeslagen datum toont de compacte datumkiezer vandaag maar staat de expliciete einddatumkeuze uit; zonder woorddoel zijn beide uitgeschakeld; na inschakelen wordt de gekozen datum opgeslagen en correct herladen.
5. Controleer toetsenbordnavigatie, accessibility name en dat er geen 01-01-1900 meer als lege toestand zichtbaar is.
6. Versie-audit: publieke stabiele release blijft 1.2.32 en actuele ontwikkelsnapshot is 1.3.0-dev.12. Meld verouderde *actuele* versieverwijzingen; historische documenten mogen hun historische versies houden.
7. `README.md` en `README_EN.md` mogen niet gewijzigd zijn.

Rapporteer blockers, regressies en kleine polish apart.
