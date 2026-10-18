# QuietWriter — releaseproces (vanaf 1.5.1)

Dit is de werkinstructie voor het uitbrengen van een QuietWriter-versie. De oude versie, met de afgeblazen SignPath-route, staat in Git en in `archive/`.

## Uitgangspunten

- **Eenvoudig, niet technisch, portable.** Gebruikers downloaden één zip, pakken die uit en starten `QuietWriter.exe`. Geen installer en geen beheerdersrechten.
- **Bijwerken via Velopack.** Een portable kopie vanaf 1.5.1 werkt zichzelf bij na de keuze **Nu bijwerken**. Velopack vervangt alleen de programmamap; boeken (werkmap), instellingen (register) en logs (`%LOCALAPPDATA%`) staan daarbuiten.
- **Eerst zelf testen, dan pas voor iedereen (vanaf 1.6.1).** Of gebruikers met één klik kunnen bijwerken, beslis je per release **op GitHub**: wel of geen `releases.win.json`. Jouw testkopie leest `releases.pilot.json` en ziet ook pre-releases. Achtergrond: `research/UPDATE_UITROL_ONDERZOEK.md`.
- **Twee repositories.** `gen-x-coder/QuietWriter-dev` (privé, werkplaats) en `gen-x-coder/QuietWriter` (publiek, releases). De app kijkt voor updates alleen naar releases van de publieke repository.
- **Unsigned.** Er is geen Authenticode-certificaat. Windows kan "onbekende uitgever" tonen. Zie `../CODE_SIGNING_POLICY.md`.
- `quietwriter/__init__.py` is de enige bron voor het versienummer. De tag is `v<versie>`, bijvoorbeeld `v1.5.1`.

## Eenmalig op de bouwcomputer

1. Python **3.12.10** en pip **26.2.1** (`build_exe.cmd` controleert dat).
2. Visual Studio Build Tools met "Desktop development with C++" (de PyInstaller-bootloader wordt uit bron gebouwd).
3. .NET SDK 8 of nieuwer, en daarna de Velopack-CLI:
   ```cmd
   dotnet tool install -g vpk --version <versie van velopack in packaging\requirements-runtime.lock>
   ```
   Bestaat precies die versie niet als `vpk`, neem dan de dichtstbijzijnde; het buildscript waarschuwt bij een verschil. Velopack raadt aan de CLI en de app-bibliotheek gelijk te houden.

## Per release

### 1. Bron klaarzetten
- [ ] Versie in `quietwriter/__init__.py` gezet (bijvoorbeeld `1.5.2`).
- [ ] `documents/CHANGELOG.md` bovenaan bijgewerkt (`## 1.5.2 — …`).
- [ ] `python -m pytest` groen; `python tools/check_locales.py` en `python tools/check_undefined_names.py` groen.
- [ ] Review afgerond (zie `../AGENTS.md`, werkwijze).
- [ ] Geen secrets, lokale instellingen of gebruikersdata in de bron.

### 2. Bouwen
```cmd
build_exe.cmd
```
Het script maakt een schone staging (allowlist), bouwt met PyInstaller (onedir), controleert de releasehygiëne en draait daarna `vpk pack`. Uitkomst:

| Bestand | Waarvoor |
|---|---|
| `release\QuietWriter-<versie>\QuietWriter.exe` | lokale test en smoke-test |
| `release\QuietWriter-windows-portable.zip` (+ `.sha256`) | download voor nieuwe gebruikers (= Velopack-`Portable.zip`) |
| `release\velopack\releases.pilot.json` | testfeed; alleen testkopieën lezen dit (stand 1) |
| `release\velopack\releases.win.json` | feed voor iedereen; pas uploaden in stand 3 |
| `release\velopack\LucasBonsel.QuietWriter-<versie>-full.nupkg` | het eigenlijke updatepakket |
| `release\velopack\*-Setup.exe` | wordt meegemaakt, maar **niet publiceren** (we blijven portable) |
| `release\QuietWriter-<versie>-build-manifest.txt` | bewijs: buildomgeving en hashes |

Alternatief: de workflow `windows-build` (handmatig starten, alleen in de publieke repository) doet hetzelfde en levert de bestanden als artifact.

### 3. Lokaal controleren (Windows)
- [ ] `release\QuietWriter-<versie>\QuietWriter.exe --smoke-test` sluit af met exitcode 0.
- [ ] Pak `QuietWriter-windows-portable.zip` uit in een **lege testmap**, start, open een bestaand boek, typ, sluit af en start opnieuw.
- [ ] Instellingen → Updates → **Nu controleren** zegt "nieuwste versie" (de nieuwe release staat nog niet online).

### 4. Publiceren in drie standen

Zet eerst de geteste bron op `QuietWriter-dev` en daarna op `QuietWriter/main`. **Neem `documents/archive/` niet mee naar de publieke repository**: die bevat interne reviews met beveiligingsdetails.

Upload de bestanden met de hand via de GitHub-website (release bewerken → bestanden erin slepen). Gebruik **niet** `vpk upload github`: dat zet `releases.win.json` meteen online, en dan sla je stand 1 en 2 over.

| Stand | Wat je doet op GitHub | 1.4.0 en ouder | Vanaf 1.5.1 | Jouw testkopie |
|---|---|---|---|---|
| **1. Test** | Nieuwe release `v<versie>`, vink **pre-release** aan. Upload `QuietWriter-windows-portable.zip` (+ `.sha256`), `LucasBonsel.QuietWriter-<versie>-full.nupkg` en `releases.pilot.json`. | ziet niets | ziet niets | **Nu bijwerken** |
| **2. Uitgebracht** | Release bewerken, **pre-release uitvinken**. Release-notities erbij. | melding + downloadpagina | melding + downloadpagina ("nog niet vrijgegeven") | — |
| **3. Bijwerken open** | `releases.win.json` uploaden bij deze (nieuwste) release. | melding + downloadpagina | **Nu bijwerken** | — |

- Stand 2 mag een paar releases duren. Upload `releases.win.json` pas als je overtuigd bent; dan geldt het voor iedereen vanaf 1.5.1, zonder nieuwe versie.
- Upload `releases.win.json` alleen bij de **nieuwste** release. Velopack kijkt naar de laatste 10 releases en neemt de hoogste versie die het vindt.
- Het pre-releasevinkje verandert niets aan de bestanden: gebruikers krijgen exact wat jij in stand 1 hebt getest.

### 5. Testkopie en updatepad controleren (stand 1)
**Eenmalig een testkopie maken:** pak een portable zip (vanaf 1.6.1) uit in een eigen map, bijvoorbeeld `C:\Temp\QW-Test\`. Zet daar een leeg bestand **`.quietwriter-update-pilot`** naast `QuietWriter.exe` en `Update.exe` (Kladblok → Opslaan als → bestandstype *Alle bestanden*). Instellingen → Updates toont dan "Testkopie". Het bestand blijft bij elke update staan.

- [ ] Start de testkopie. Instellingen → Updates → **Nu controleren** → **Nu bijwerken**.
- [ ] Verwacht: voortgang, QuietWriter sluit, Velopack werkt bij, QuietWriter start opnieuw met de nieuwe versie (zie Over).
- [ ] Boeken, instellingen, thema en Meelezer-instellingen zijn onveranderd.
- [ ] Een gewone kopie (zonder pilotbestand) ziet bij **Nu controleren** géén nieuwe versie.
- [ ] Na stand 2: de vaste link `https://github.com/gen-x-coder/QuietWriter/releases/latest/download/QuietWriter-windows-portable.zip` levert de nieuwe zip.
- [ ] Na stand 3: een gewone kopie vanaf 1.5.1 biedt **Nu bijwerken** aan.

Gaat er in stand 1 iets mis: verwijder de pre-release. Geen gebruiker heeft hem gezien.

## Bijwerken testen zonder GitHub

Met de omgevingsvariabele `QUIETWRITER_UPDATE_SOURCE` kijkt QuietWriter niet op GitHub maar in een lokale map met `vpk pack`-uitvoer. Een testkopie leest daar `releases.pilot.json`, een gewone kopie `releases.win.json`; het buildscript maakt ze allebei.

1. Bouw versie A (bijvoorbeeld 1.6.1) en pak `release\QuietWriter-windows-portable.zip` uit in `C:\Temp\QW-A\`.
2. Zet in `quietwriter\__init__.py` tijdelijk een hogere versie, bijvoorbeeld `1.6.2`, en bouw opnieuw. `release\velopack\` bevat nu de feed voor 1.6.2.
3. Start A met de lokale bron:
   ```cmd
   set QUIETWRITER_UPDATE_SOURCE=C:\Users\lucas\OneDrive\Desktop\Projects\QuietWriter-dev\release\velopack
   C:\Temp\QW-A\QuietWriter.exe
   ```
4. Instellingen → Updates → **Nu controleren** → **Nu bijwerken**. Verwacht: voortgang, QuietWriter sluit, werkt bij en start als 1.6.2. Boeken en instellingen zijn onveranderd.
5. Zet `__version__` terug en verwijder de testmap.

De variabele werkt alleen in het venster waarin je hem zet; gewone gebruikers merken er niets van. Een GitHub-adres mag ook (`https://github.com/<eigenaar>/<repo>`).

## Overstap van oudere versies (eenmalig)

Kopieën van vóór 1.5.1 en de bronversie kunnen zichzelf niet bijwerken. Ze melden de nieuwe versie en openen GitHub. De gebruiker pakt de nieuwe zip uit in een nieuwe map en start die. Boeken en instellingen staan buiten de programmamap en worden gewoon gevonden. De oude map mag daarna weg.

## Als het misgaat

- **Fout vóór publicatie:** niets publiceren, oorzaak oplossen, opnieuw bouwen.
- **Fout in stand 1:** pre-release verwijderen, oplossen, opnieuw bouwen. Niemand heeft hem gezien.
- **Fout in stand 2 of 3:** de tag niet verplaatsen. Verwijder `releases.win.json` uit de release (één klik bijwerken stopt meteen) en maak een nieuwe patchversie. Gebruikers die al bijgewerkt zijn, krijgen die patchversie. QuietWriter zet nooit een lagere versie terug.

## Linux

De tests draaien ook op Ubuntu, maar Windows is het enige officiële platform. Een Linux-build (Velopack kan een AppImage maken) komt pas na een eigen praktijktest.
