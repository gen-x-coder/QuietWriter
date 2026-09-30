# QuietWriter: logo- en iconenpakket

Alle bestanden komen uit de twee originele logo-SVG's. De vorm is niet opnieuw getekend. Alleen de kleine variant (16–24
px) is vereenvoudigd: dikkere lijnen, bredere spleten en zonder het krulletje bovenaan de rug. Zie `overzicht.png`.

## Wat zit erin

| Bestand | Gebruik |
|---|---|
| `quietwriter.ico` | **Het app-icoon**: `.exe`, venster en taakbalk. Bevat 10 formaten (16–256 px). Voor 16/20/24 px wordt het kleine ontwerp gebruikt, vanaf 32 px het volle detail. Het icoon staat op een tegel in de accentkleur van *Helder* (`#4d738f`), zodat het leesbaar is op zowel een lichte als een donkere taakbalk. |
| `png/quietwriter-{16…1024}.png` | Dezelfde tegel als losse PNG's (README, website, Linux/macOS later). |
| `svg/quietwriter-app-tegel.svg` / `-klein.svg` | De bron van de tegel: vol detail en de vereenvoudigde variant. |
| `svg/quietwriter-icoon-{donker,licht}.svg` | Het embleem op een vierkant, transparant canvas. |
| `svg/quietwriter-icoon-klein-{donker,licht}.svg` | Vereenvoudigd embleem, vierkant, voor 16–24 px. |
| `svg/quietwriter-embleem-{donker,licht}.svg` | Het embleem in de originele verhouding (765×1135), zonder canvas. |
| `svg/quietwriter-woordmerk-{donker,licht}.svg` | Embleem met "QuietWriter" (splash, Over, README). |
| `in-app/*.svg` | Voor `quietwriter/icons/`: krijgt automatisch de themakleur (zie hieronder). |
| `bron/` | De originelen plus `maak_iconen.py`, dat alles hierboven opnieuw maakt. Een andere tegelkleur? Pas `ACCENT` aan in `logo_geometrie.py`. |

Donker = `#20242a` (tekstkleur van Helder). Licht = `#f4f5f7` (achtergrond van Helder).

## Inbouwen

**1. Venster- en taakbalkicoon.** Zet `quietwriter.ico` in bijvoorbeeld `quietwriter/resources/`. Vervang `icon('books')`
in `app.py` (regel 39) en `ui/main_window.py` (regel 50):

```python
app.setWindowIcon(QIcon(str(Path(__file__).with_name('resources') / 'quietwriter.ico')))
```

Op Windows toont de taakbalk bij `python main.py` anders het **Python-icoon**. Zet daarom vóór het aanmaken van de
`QApplication` een eigen AppUserModelID:

```python
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('LucasBonsel.QuietWriter')
```

**2. Het `.exe`-icoon** (PyInstaller): `--icon quietwriter/resources/quietwriter.ico`. Neem het `.ico` óók mee als
databestand, want stap 1 laadt het tijdens het draaien.

**3. In de app** (splash, Over, first-run): kopieer `in-app/quietwriter.svg` en `in-app/quietwriter-small.svg` naar
`quietwriter/icons/`. `_recolour_svg` in `icon_theme.py` kleurt ze dan per thema in. Getest in alle 14 thema's, zie
`overzicht.png`.

```python
icon('quietwriter', 48)      # geef de grootte expliciet mee; standaard rendert icon() op 24 px
icon('quietwriter-small')    # voor 16–24 px
```

**4. Woordmerk** (splash, Over): gebruik hiervoor **niet** `icon()`, want dat rendert op een vierkant en zou het
woordmerk uitrekken. Render de SVG zelf in verhouding 1939:487:

```python
raw = _recolour_svg((ICON_DIR / 'quietwriter-wordmark.svg').read_text('utf-8'), theme['text'])
QSvgRenderer(QByteArray(raw.encode())).render(painter, QRectF(0, 0, 256, 256 * 487 / 1939))
```

## Opmerkingen

- Het `.ico` bevat PNG-gecomprimeerde afbeeldingen. Dat ondersteunt Windows sinds Vista, en PyInstaller en Qt lezen het
  zonder problemen (gecontroleerd: Qt ziet alle 10 formaten).
- Er zit bewust geen `clip-path` in de SVG's. Qt's SVG-renderer ondersteunt dat niet, dus alles bestaat uit gewone
  paden.
