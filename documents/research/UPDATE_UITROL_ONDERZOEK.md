# Onderzoek: bijwerken eerst zelf testen, daarna pas voor gebruikers

**Datum:** 15 oktober 2026 (Claude, na 1.6.0)
**Vraag van Lucas:** kan ik bijwerken via de echte GitHub testen zonder dat gewone gebruikers automatisch bijwerken? Kan het bijwerken een paar releases standaard uit blijven, zoals vroeger met `.quietwriter-update-pilot`?

## 1. Feiten (nagelezen in de broncode van Velopack 1.2.161)

| Onderwerp | Hoe Velopack het doet | Bron |
|---|---|---|
| Waar het zoekt | De laatste **10** GitHub-releases. Pre-releases worden overgeslagen, behalve met `GithubSource(..., prerelease=True)`. | `sources/github.rs`, `get_releases` |
| Welk bestand | Per release het bestand `releases.{kanaal}.json`. Het kanaal is standaard `win`, of `UpdateOptions.ExplicitChannel`. Een release **zonder** dat bestand slaat Velopack stil over; dat geeft geen fout. | `sources/mod.rs`, `get_git_release_feed` |
| Samenvoegen | Velopack voegt de feeds van al die releases samen en neemt de hoogste volledige versie. | idem |
| Downloaden | De bestandsnaam van het pakket komt uit de feed. Velopack zoekt dat bestand in alle releases. | `github.rs`, `download_release_entry` |
| Terug naar een lagere versie | Alleen met `AllowVersionDowngrade`; dat staat standaard uit. | `manager.rs`, `check_for_updates` |
| Wat bijwerken aanraakt | Alleen de map `current\`. Bestanden ernaast (naast `Update.exe`) blijven staan. | `apply_windows_impl.rs`, `replace_current_dir` |
| Geleidelijke uitrol ("staged rollout") | Bestaat alleen in de betaalde dienst Velopack Flow. Niet voor GitHub. | `sources/flow.rs` |

Ook vastgesteld:
- **QuietWriter 1.4.0 en de oude melding** vragen GitHub om `/releases/latest`. Dat geeft nooit een pre-release (en `update_checker.py` filtert ze ook nog zelf). Een pre-release is dus onzichtbaar voor 1.4.0-gebruikers.
- De vaste downloadlink `/releases/latest/download/...` wijst ook nooit naar een pre-release.

## 2. Antwoorden op de vragen

**Kan het met 1.4.0?** Nee, niet als startversie. Er zit geen Velopack in 1.4.0. Die kopie toont alleen "nieuwe versie" en opent de downloadpagina. Dat werkt al en hoeft niet getest te worden.

**Hebben we 1.5.0 nodig?** Nee. De **startversie** moet een Velopack-build zijn (vanaf 1.5.1). Die hoeft nooit gepubliceerd te zijn: een eigen build die je uitpakt, is genoeg. Alleen de **doelversie** moet op GitHub staan.

**Simuleren?** Dat doen we al met `QUIETWRITER_UPDATE_SOURCE` en een lokale map; jouw proef 1.5.2 → 1.5.3 werkte. Het enige verschil met GitHub is het ophalen van de lijst (de GitHub-API). Een nep-GitHub bouwen kost meer dan het oplevert. Een echte test met een pre-release is eenvoudiger en dekt precies dat stuk.

**Was het pilotbestand onzin?** Nee, het idee klopt. Eén ding moet anders. Als de "uit"-schakelaar **in de app** zit, beslist de *geïnstalleerde* versie. Wie 1.6.x met de schakelaar uit heeft, krijgt later nooit vanzelf de versie waarin hij aan staat. Iedereen moet dan nog één keer handmatig overstappen. Beter: de schakelaar ligt **op GitHub**, per release.

## 3. Aanbevolen aanpak: twee feeds, één build

`build_exe.cmd` maakt naast `releases.win.json` een kopie met de naam **`releases.pilot.json`**. De inhoud is gelijk.

| Kopie | Kijkt naar | Ziet |
|---|---|---|
| **Gewone gebruiker** | stabiele releases, `releases.win.json` | alleen een release waar jij `releases.win.json` bij hebt gezet |
| **Jouw testkopie** (bestand `.quietwriter-update-pilot` naast `QuietWriter.exe`) | ook pre-releases, `releases.pilot.json` | elke versie die je uploadt, al vóór publicatie |

Het pilotbestand staat in de portable map naast `Update.exe`. Velopack vervangt alleen `current\`, dus het bestand blijft na elke update staan.

### Een release in drie standen (allemaal op GitHub, zonder nieuwe build)

| Stand | Wat je uploadt | Gebruikers 1.4.0 | Gebruikers vanaf 1.5.1 | Jouw testkopie |
|---|---|---|---|---|
| **1. Test** | Pre-release met zip + `.nupkg` + `releases.pilot.json` | niets | niets | **Nu bijwerken** via de echte GitHub |
| **2. Uitgebracht, bijwerken dicht** | Pre-release wordt release | melding + downloadpagina | melding + downloadpagina | — |
| **3. Bijwerken open** | `releases.win.json` erbij uploaden | melding + downloadpagina | **Nu bijwerken** | — |

- Je wens "de komende 2–3 releases standaard uit" wordt: **stand 2** gebruiken en `releases.win.json` niet uploaden.
- Ben je overtuigd, dan upload je `releases.win.json` bij de **nieuwste** release. Vanaf dat moment werkt iedereen met 1.5.1 of nieuwer met één klik bij. Daar is geen nieuwe versie en geen handmatige overstap voor nodig.
- **Terugdraaien:** verwijder `releases.win.json` uit de nieuwste release. Velopack biedt dan hoogstens de vorige "open" release aan en gaat nooit omlaag.
- Je test **exact het bestand** dat gebruikers krijgen. Het pre-releasevinkje uitzetten verandert niets aan de bestanden.

### Wat er in de code moet (klein, ~1 uur) — gebouwd in 1.6.1
1. `self_update.py`: pilotbestand herkennen. Dan `GithubSource(..., prerelease=True)` en `UpdateOptions(False, 0, 'pilot')`.
2. `main_window.py`: vindt Velopack bij een **automatische** controle niets, vraag dan stil GitHub. Nu gebeurt dat alleen bij "Nu controleren". Zonder deze stap krijgen gebruikers in stand 2 bij het opstarten geen melding.
3. `build_exe.cmd`: maak `releases.pilot.json` en controleer dat die er staat.
4. Instellingen → Updates: toon "Testkopie: ziet ook testversies" als het pilotbestand er is.
5. Tests, plus `RELEASE_PROCESS.md` herschrijven naar de drie standen.

## 4. Overwogen en afgewezen

| Optie | Waarom niet |
|---|---|
| Uit-schakelaar als constante in de code | Kost gebruikers later een extra handmatige overstap (zie §2). |
| Alleen pre-release als testmiddel | Werkt voor jouw test, maar zodra je publiceert werkt bijwerken meteen voor iedereen. Dan kun je het niet een paar releases dicht houden. |
| Twee builds met `vpk pack --channel pilot` | Twee verschillende bestanden: je test dan niet wat gebruikers krijgen. |
| Aparte test-repository | Werkt, maar geeft extra beheer. Een pre-release in de publieke repository is al onzichtbaar voor gebruikers. |
| Velopack Flow (geleidelijke uitrol) | Betaald en een externe dienst; past niet bij "eenvoudig". |
| Nep-GitHub voor automatische tests | Veel werk voor het enige stuk dat een echte pre-release-test al dekt. |

## 5. Eerste echte test (voorstel)
1. Bouw 1.6.1 met de wijzigingen hierboven. Pak de zip uit in `C:\Temp\QW-A\` en zet daar een leeg bestand `.quietwriter-update-pilot` naast `QuietWriter.exe`.
2. Zet tijdelijk `1.6.2` als versie en bouw opnieuw. Maak op GitHub een **pre-release** `v1.6.2-test` met de zip, de `.nupkg` en `releases.pilot.json`.
3. Start `C:\Temp\QW-A\QuietWriter.exe` en kies **Nu controleren** → **Nu bijwerken**. Verwacht: 1.6.2, met boeken en instellingen ongewijzigd.
4. Controleer dat een kopie **zonder** pilotbestand niets ziet. Een 1.4.0-kopie ziet ook niets.
5. Verwijder de test-pre-release. Dat mag: geen gebruiker heeft hem gezien.
