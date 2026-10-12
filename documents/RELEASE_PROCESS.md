# QuietWriter – releaseproces

De publieke stabiele code staat op de beschermde branch `main`. Ontwikkelwerk vindt plaats in de privé-repository `QuietWriter-dev`. Wijzigingen naar `main` lopen via een pull request en de vereiste integriteitschecks.

1. Controleer de applicatieversie in `quietwriter/__init__.py` en voeg de stabiele versie bovenaan `documents/CHANGELOG.md` toe.
2. Controleer dat de publieke `README.md`, `README_EN.md` en `branding/` ongemoeid zijn gebleven; pas ze uitsluitend bewust aan, inclusief hun goedgekeurde integriteitscontroles.
3. Voer de volledige tests op Windows en Linux uit; verifieer de Windows portable build met de smoke-test.
4. Maak een tag `vX.Y.Z` op de exacte geteste releasecommit. Een tag mag niet naar de vorige release verwijzen.
5. Publiceer de Windows-ZIP op de corresponderende GitHub-release, met bij voorkeur een afzonderlijk SHA-256-bestand; controleer naam, inhoud en herkomst van de ZIP.
6. Publiceer de release als stabiel en verifieer dat `/releases/latest` en de updatechecker naar de bedoelde versie verwijzen.
7. Verwijder tijdelijke releasebranches wanneer ze niet meer nodig zijn. Houd historische tags en releases intact.

Zie ook `RELEASE_CHECKLIST.md` en `RELEASE_BRANDING_AND_OPERATIONS.md`.
