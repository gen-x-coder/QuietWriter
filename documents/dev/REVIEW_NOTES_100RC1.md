# Review notes 1.0.0-rc1

## Doel

Release-only omzetting van de groen verklaarde 0.36.10 naar de eerste release candidate. Feature freeze blijft van kracht: geen nieuwe productfunctionaliteit.

## Gewijzigd

- `quietwriter.__version__` naar `1.0.0-rc1`.
- CHANGELOG-kop gecorrigeerd en RC1-sectie toegevoegd.
- Publieke release notes toegevoegd met bekende beperking en expliciet nog niet afgeronde praktijktests.
- GitHub-tagrelease gebruikt deze release notes als body; een tag met `rc` blijft automatisch pre-release.
- `LEESMIJ.txt` benoemt expliciet dat dit een release candidate is en adviseert extra back-ups tijdens de testperiode.
- Windows numeric file version gebruikt alleen SemVer core (`1.0.0.0`), terwijl de strings `1.0.0-rc1` tonen. Daardoor kan de latere stabiele `1.0.0` niet numeriek lager worden dan RC1.
- Review 55 opgenomen in `documents/dev/`.

## Expliciet niet gewijzigd

- Geen editor-, opslag-, AI-, export-, UI- of providerlogica gewijzigd.
- Het kleine OpenRouter-weergaveverschil bij een bewaard betaald model + actief gratis-filter blijft als bekende niet-blokkerende beperking voor na RC1.

## Reviewfocus voor Claude

1. Versie `1.0.0-rc1` consequent in package, staging, buildmap, ZIP en Windows string-version metadata.
2. Windows fixed file version is `1.0.0.0` en niet `1.0.0.1`.
3. CHANGELOG begint met `# Changelog` en daarna RC1.
4. GitHub-release bij tag `v1.0.0-rc1` is pre-release en gebruikt `documents/RELEASE_NOTES_1.0.0-rc1.md`.
5. Geen functionele diff buiten release/version/documentatie en numeric version parsing.
6. De vier testsuites, undefined-name checker, koude start en `--smoke-test` opnieuw groen.
