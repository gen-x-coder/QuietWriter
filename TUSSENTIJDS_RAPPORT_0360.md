# Tussentijds rapport 0.36.0

## Doel

De ontwikkelomgeving hoeft niet meer opgeruimd te worden om een distributie te maken. QuietWriter krijgt een expliciete scheiding tussen werkplaats en release.

## Ontwerp

`tools/prepare_release.py` gebruikt een allowlist. Het wist `release/stage` volledig en kopieert alleen de applicatiebron, packagingconfiguratie, twee resource-downloadtools, fontmetadata en licenties. De stage wordt gevalideerd en krijgt een hashmanifest.

`build_exe.cmd` bouwt daarna uitsluitend vanuit deze stagingmap. De uiteindelijke PyInstaller-map wordt naar `release/QuietWriter-<versie>` gekopieerd en gezipt. PPM, tests, Git-metadata en reviewdocumenten worden nogmaals als release-hygiene gecontroleerd.

## Claude packaging package

Overgenomen als basis:
- `packaging/quietwriter.spec`
- `packaging/make_version_info.py`
- `tools/fetch_dictionaries.py`
- `build_exe.cmd` (aangepast naar staging)
- `.github/workflows/build-windows.yml` (aangepast naar dezelfde lokale buildroute)
- aangevulde `THIRD_PARTY_LICENSES.md`

## Lokale verificatie in deze omgeving

De staging is daadwerkelijk opgebouwd en `--check` is groen. De gegenereerde stage bevat geen testmap, PPM of historische reviewrapporten. Een echte Windows `.exe` kan in deze Linux-omgeving niet betrouwbaar met PyInstaller worden gebouwd; dat is expliciet een Windows-reviewpunt.
