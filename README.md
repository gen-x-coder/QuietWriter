# QuietWriter

QuietWriter is een lokale desktop-schrijfomgeving voor boeken en langere teksten. De applicatie combineert een rustige editor met Planning, revisiegeschiedenis en herstel, spelling, publicatie/export, media en een optionele **AI Meelezer** voor feedback, feiten, consistentie en persona-/stijlcontrole.

**Huidige stabiele versie:** 1.1.0.

## Download

Zie ook [DOWNLOAD.md](DOWNLOAD.md) voor de officiële downloadlocatie en informatie over code signing.

De nieuwste stabiele Windows-versie staat onder **Releases**. De vaste downloadlink is:

https://github.com/gen-x-coder/QuietWriter/releases/latest/download/QuietWriter-windows-portable.zip

Pak de ZIP volledig uit voordat je QuietWriter start.

## Broncode

QuietWriter wordt vanaf versie 1.1.0 als open-sourceproject gepubliceerd. De publieke repository is de bron voor stabiele releases. Actieve ontwikkeling vindt plaats in een afzonderlijke ontwikkelrepository en wordt na validatie als nieuwe versie naar deze repository gebracht.

Python 3.12+:

```bash
python -m pip install -r requirements.txt
python main.py
```

Voor ontwikkeling en tests:

```bash
python -m pip install -r requirements-dev.txt
python tools/check_undefined_names.py
pytest
pytest -m qt
```

## Windows-build

```bat
build_exe.cmd
```

De build maakt een portable Windows-versie onder `release/`.

## Privacy en AI

QuietWriter is ontworpen als lokale schrijfapp. Boeken en werkbestanden blijven lokaal tenzij de gebruiker bewust een externe AI-provider gebruikt.

- **Ollama** kan volledig lokaal draaien.
- Bij **OpenRouter** wordt pas context verstuurd wanneer de gebruiker bewust een vraag aan de Meelezer stelt.
- De Meelezer is bedoeld als tweede lezer, niet als autonome co-auteur.

## Privacy

Zie [PRIVACY.md](PRIVACY.md) voor het privacybeleid van QuietWriter.

## Code signing

QuietWriter is momenteel nog niet digitaal ondertekend. Het project werkt toe naar reproduceerbare, geautomatiseerde Windows-builds met openbare herkomstcontrole.

Free code signing provided by SignPath.io, certificate by SignPath Foundation.

Zie `CODE_SIGNING_POLICY.md`.

## Licentie

QuietWriter is vrije software onder de **GNU General Public License v3.0 (GPLv3)**. Zie `LICENSE`.

Componenten van derden behouden hun eigen licenties. Zie `documents/licenses/THIRD_PARTY_LICENSES.md` zodra de broncode van 1.1.0 in deze repository is gepubliceerd.
