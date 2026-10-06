# QuietWriter branding

Deze map bevat de **bron** waaruit de QuietWriter-branding reproduceerbaar wordt gegenereerd. Bewerk afgeleide app-iconen niet handmatig als dezelfde wijziging in de bron kan worden gedaan.

## Canonieke bron

In `branding/bron/`:

- `emblem_src.svg` — origineel embleem;
- `wordmark_src.svg` — origineel woordmerk;
- `logo_geometrie.py` — geometrie, tegelkleur en kleine iconvariant;
- `maak_iconen.py` — genereert de afgeleide iconen en previews.

`branding/overzicht.png` is een visuele controle van de gegenereerde set.

## Genereren

Installeer eerst de ontwikkelvereisten:

```bash
python -m pip install -r requirements-dev.txt
```

De generator gebruikt onder andere `shapely`.

Voer daarna vanuit de projectroot uit:

```bash
python branding/bron/maak_iconen.py
```

De generator maakt de volledige brandset. Relevante gegenereerde bestanden voor de applicatie worden vervolgens gebruikt in:

- `quietwriter/resources/quietwriter.ico` — Windows EXE/venster/taakbalk;
- `quietwriter/icons/quietwriter.svg` — normaal in-app embleem;
- `quietwriter/icons/quietwriter-small.svg` — vereenvoudigde variant voor kleine maten;
- `quietwriter/icons/quietwriter-wordmark.svg` — splash/Over-pagina.

De kleine variant is bewust vereenvoudigd voor ongeveer 16–24 px. Het woordmerk heeft een horizontale verhouding en moet niet via een vierkante iconrenderer worden vervormd.

## Thema en HiDPI

In-app SVG's worden door `quietwriter/icon_theme.py` naar de actieve semantische themakleur omgezet. Houd dus geen aparte handgemaakte kleurset per thema bij.

Controleer brandingwijzigingen minimaal op 100%, 125% en 150% Windows-schaal. Een correcte SVG-bron is niet automatisch een scherpe pixmap als de device-pixel-ratio verkeerd wordt toegepast.

## Wijzigingsregel

Bij een brandingwijziging:

1. wijzig de bron-SVG/geometrie;
2. draai `maak_iconen.py`;
3. controleer `overzicht.png` en kleine iconmaten;
4. controleer de bestanden in `quietwriter/icons/` en `quietwriter/resources/`;
5. commit bron en relevante gegenereerde uitvoer samen.
