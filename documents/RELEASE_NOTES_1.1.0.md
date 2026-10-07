# QuietWriter 1.1.0

QuietWriter 1.1.0 is de eerste stabiele feature-release na 1.0.0. De release bouwt voort op de volledig geteste 1.0.23-bronbasis.

## Nieuw sinds 1.0.0

- **Bewaarplaats / Darlings**: fragmenten bewaren, terugplaatsen, knippen en herstellen zonder het schrijfproces te verliezen.
- **Begeleide first-run**: live themapreview, optionele rondleiding en veilig herstellen van standaardinstellingen.
- **Updatecontrole**: handmatig altijd beschikbaar en automatisch alleen na opt-in.
- **DOCX import en export**: hoofdstukstructuur, ondersteunde opmaak, taalmetadata, omslag en veilige afbeeldingsschaal.
- **`.qwbook`**: compleet overdraagbaar boekformaat met integriteitscontrole, veilige import, optionele versiegeschiedenis en back-upherstel.
- Veel extra regressietests en data-integriteitscontroles.

## Windows-build en veiligheid

De Windows portable release blijft een **onedir** PyInstaller-build met `upx=False` en `console=False`. Vanaf 1.1.0 wordt PyInstaller vastgezet op 6.22.3 en wordt de bootloader lokaal uit bron gecompileerd om generieke antivirus-false-positives te helpen verminderen. Dit is geen garantie tegen heuristische meldingen.

Na elke build worden SHA-256 hashes van zowel de losse exe als de release-ZIP vastgelegd.

## Geen automatische installatie

De updatecontrole meldt alleen dat er een nieuwere stabiele versie beschikbaar is. QuietWriter downloadt of installeert updates niet automatisch.
