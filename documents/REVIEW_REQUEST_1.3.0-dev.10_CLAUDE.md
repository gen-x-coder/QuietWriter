# Reviewopdracht QuietWriter 1.3.0-dev.10

Wijzig geen code. Dit is bedoeld als laatste release-polishreview vóór het vastzetten van 1.3.0.

## Context

Lucas heeft 1.3.0-dev.9 op Windows visueel en functioneel getest en geen problemen gevonden, inclusief echte Boekenkast-interactie en covers. Daarom is cover-pixmapcaching bewust niet toegevoegd. Dev.10 verandert geen productfunctionaliteit.

## Controleer

1. Draai de volledige pytest-suite en meld passed/failed én de uiteindelijke exitcode. Vergelijk de bekende Linux Qt-teardown rc 139 met dev.9.
2. Draai `python main.py --smoke-test`.
3. Controleer locales (1551 sleutels in 5 talen), undefined names en pyflakes; vergelijk pyflakes met dev.9.
4. Controleer dat `quietwriter.__version__`, `SNAPSHOT_INFO.txt`, release notes en relevante metadata-tests allemaal `1.3.0-dev.10` noemen.
5. Controleer `packaging/requirements-runtime.lock` en `packaging/requirements-build.lock`:
   - alleen de verouderde eerste kopregel hoort inhoudelijk te zijn aangepast;
   - dependency-versies moeten byte-/regelinhoudelijk verder gelijk zijn aan dev.9;
   - er mag nergens in `packaging/*.lock` nog `1.2.32 Windows RC` staan.
6. Controleer dat er geen functionele wijzigingen zijn in Boekenkast, Presentatiemodus of de woordtellingcache ten opzichte van dev.9. Een gerichte diff is hiervoor voldoende.
7. Herhaal minimaal de relevante dev.9 cache-/Presentatiemodus-harnassen als praktische regressiecontrole.
8. Controleer dat `.pytest_cache` en `__pycache__` niet in de ZIP zitten.
9. Controleer dat `README.md` byte-identiek is aan dev.9 en dat `README_EN.md` niet is aangemaakt als die in dev.9 niet aanwezig was.

## Beoordeling

Classificeer bevindingen als:
- blocker vóór 1.3.0;
- klein releasepunt vóór 1.3.0;
- veilige backlog voor 1.4.x.

Beantwoord expliciet de vraag: **is 1.3.0-dev.10 na deze review geschikt om zonder verdere functionele dev-build als basis voor de 1.3.0-release te dienen?**
