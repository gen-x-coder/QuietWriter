# QuietWriter — developer reference

Status: praktische naslag voor 1.0.0-rc5. Voor productkeuzes en veiligheidsredenen zie ook `PROJECT_GUIDE.md`, `ARCHITECTURE_AND_DATA_SAFETY.md` en `PRODUCT_AND_UI_PHILOSOPHY.md`.

## 1. Starten

QuietWriter vereist Python 3.12 of nieuwer.

```bash
python -m pip install -r requirements.txt
python main.py
```

Voor ontwikkeling/tests:

```bash
python -m pip install -r requirements-dev.txt
python tools/fetch_bundled_fonts.py
pytest
```

## 2. Opdrachtregelvlaggen

QuietWriter kent drie eigen switches.

### `--profile prod|dev`

Kiest het runtimeprofiel.

```bash
python main.py --profile prod
python main.py --profile dev
```

Ook mogelijk:

```bash
python main.py --profile=dev
```

Zonder expliciete vlag wordt `QUIETWRITER_PROFILE` gelezen. Onbekende profielwaarden vallen veilig terug op `prod`.

### `--first-run`

Toont de first-run wizard bewust opnieuw voor testdoeleinden zonder eerst echte instellingen te verwijderen.

```bash
python main.py --first-run
```

### `--smoke-test`

Doorloopt de echte applicatiestart in een hermetische tijdelijke omgeving en sluit automatisch. Het smokeprofiel gebruikt geen echte gebruikerinstellingen of werkmap.

```bash
python main.py --smoke-test
```

Normaal resultaat: exitcode 0. Een startup- of eventloopfout geeft een niet-nul exitcode en hoort niet op een modale dialoog te blijven hangen.

## 3. Runtimeprofielen

### Productie

- profielkey: `prod`
- QSettings application: `QuietWriter`
- Qt application name: `QuietWriter`
- standaardwerkmap: `~/QuietWriter`
- Windows AppUserModelID: `LucasBonsel.QuietWriter`

### Development

- profielkey: `dev`
- QSettings application: `QuietWriter-Dev`
- Qt application name: `QuietWriter Dev`
- standaardwerkmap: `~/QuietWriter-Dev`
- Windows AppUserModelID: `LucasBonsel.QuietWriter.Dev`

Een door de gebruiker gekozen `workspace` overschrijft de standaardwerkmap. Relatieve paden worden onder de homefolder geïnterpreteerd, nooit onder de programmamap.

## 4. Instellingen en logs

QuietWriter gebruikt `QSettings('QuietWriter', <profile application>)`.

Op Windows betekent dit normaal instellingen onder het gebruikersprofiel/Windows-register voor organisatie `QuietWriter`, met applicatie `QuietWriter` of `QuietWriter-Dev`.

Crashlogging gebruikt Qt `AppLocalDataLocation` en schrijft naar:

```text
<local app data>/logs/crash.log
```

Voor het productieprofiel is de gangbare Windowslocatie:

```text
%LOCALAPPDATA%\QuietWriter\QuietWriter\logs\crash.log
```

Gebruik in code altijd `QStandardPaths`/de bestaande runtimeprofile-route en bouw dit pad niet hardcoded opnieuw op.

## 5. Belangrijke settingskeys

Huidige veelgebruikte keys zijn onder meer:

### Algemeen / UI
- `language`
- `theme`
- `workspace`
- `geometry`
- `windowState`
- `splitter`
- `nav_expanded`
- `right_visible`
- `toolrail_expanded`
- `advanced_options`
- `first_run_done`

### Schrijven
- `editor_font`
- `editor_font_size`
- `editor_text_width`
- `manuscript_indent`
- `manuscript_line_spacing`
- `manuscript_paragraph_spacing`
- `manuscript_visible`
- `smart_quotes`

### Spelling
- `spell_enabled`
- `spell_language`
- `spell_dictionary`

### AI
- `ai_enabled`
- `ai_provider`
- `ai_disable_thinking`
- `ai_quick_actions_expanded`
- `ai_use_chapter_planning`
- `ollama_url`
- `ollama_model`
- `openrouter_url`
- `openrouter_model`
- `openrouter_free_only`
- `openrouter_api_key`

### Export
- `export/output_dir`

**Let op:** de OpenRouter API-key wordt momenteel als gewone QSettings-waarde bewaard. Op Windows is dat geen versleutelde credential store. Behandel het gebruikersprofiel/registry daarom als gevoelige lokale data en log de sleutel nooit.

## 6. Werkmapstructuur

Een nieuwe `Library` maakt in de werkmap minimaal deze structuur:

```text
<workspace>/
  books/
  boekomslagen/          # legacy/global cover compatibility
  archive/
  trash/
  persona/
    schrijver.md
  dictionaries/
  .cache/
```

`persona/schrijver.md` is de globale Schrijverspersona.

`.cache/` bevat niet-autoritatieve data zoals de zoekindex. Een cache moet weggooibaar en herbouwbaar blijven.

`archive/` (waaronder `archive/persona/` voor globale persona-herstelkopieën) en `trash/` zijn onderdeel van herstel-/verwijderflows; behandel ze niet als tijdelijke builddata.

## 7. Boekmap

Een boek leeft onder:

```text
<workspace>/books/<slug>-<id8>/
```

Bij creatie bestaat minimaal:

```text
book.json
chapters/
  <chapter-uuid>.md
assets/
  manifest.json
  images/
  cover/
```

Andere onderdelen worden wanneer nodig toegevoegd.

Een representatieve uitgebreide boekmap kan bevatten:

```text
book.json
chapters/
planning/
  characters.json
  outline.json
  notes.md
publication/
  publication.json
  texts/
export/
  settings.json
ai/
  boekprofiel.md
  memory.md
.quietwriter/
  ai_chat.json
assets/
  manifest.json
  images/
  cover/
```

Niet ieder bestand bestaat in ieder boek. Code moet afwezigheid onderscheiden van corruptie.

## 8. `book.json`

Het huidige boekformaat is format 2.

Hoofdvelden:
- `format`
- `id`
- `title`
- `metadata`
- `sections`

Een sectie bevat een `id`, titel en hoofdstukken. Een hoofdstuk bevat een id, titel en relatief pad onder `chapters/`.

Onbekende top-level manifestkeys worden bewaard voor veilige round-trips waar de huidige formatgrens dit toelaat.

Een boek met een **nieuwer** format dan QuietWriter begrijpt is future-format, niet corrupt. Niet downgraden of stil herschrijven.

## 9. Planning

Belangrijkste bronnen:

```text
planning/characters.json
planning/outline.json
planning/notes.md
```

Planning is intentie en structuur, niet het manuscript.

Structureel ongeldige of nieuwere Planning hoort zoveel mogelijk read-only te degraderen zonder het hele boek onbruikbaar te maken.

## 10. Publicatie en export

Publicatiestructuur:

```text
publication/publication.json
publication/texts/*.md
```

Exportinstellingen per boek:

```text
export/settings.json
```

Publicatie beschrijft semantische voor-/achterwerkstructuur. De exportmodules bepalen rendering naar EPUB/PDF/Markdown.

## 11. AI-bestanden

```text
ai/boekprofiel.md
ai/memory.md
.quietwriter/ai_chat.json
```

- `boekprofiel.md`: kader voor dit specifieke boek;
- `memory.md`: duurzame boekkennis/besluiten;
- `ai_chat.json`: lokale gesprekstate.

De globale Schrijverspersona staat buiten het boek in de werkmap.

## 12. Media

Boekmedia gebruikt:

```text
assets/manifest.json
assets/images/
assets/cover/
```

Het manifest is revision-guarded. Binaire assets worden niet bij iedere save volledig gehasht.

Media Manager is bewust conservatief: een onzekere of onleesbare verwijzing is geen bewijs dat een bestand ongebruikt is.

Beschermde mediablokken in de editor zijn presentatie; leesbare Markdown blijft de canonieke bron.

## 13. Revisions, History en archive

QuietWriter gebruikt optimistic concurrency in plaats van permanente lockfiles.

Voor writes:
- actuele revision vergelijken met baseline;
- bij externe wijziging niet stil overschrijven;
- waar passend drie-wegs merge;
- lokale conflictstate eerst veiligstellen.

History/checkpoints hebben verschillende soorten, waaronder conflict/recovery/migration. Niet iedere snapshot is automatisch een geldige herstelbron.

## 14. Zoekcache

De zoekindex is cache en dus niet autoritatief.

Bij corrupte SQLite-header of openfout:
- verbinding netjes sluiten;
- cache verwijderen/herbouwen;
- manuscript blijft bron van waarheid.

Windows-handlecleanup is belangrijk; een `sqlite3` contextmanager alleen sluit de verbinding niet automatisch.

## 15. Vertaling

Zichtbare UI-tekst gebruikt de gedeelde `tr()`-route en locale-JSON-bestanden:

```text
quietwriter/locales/nl.json
quietwriter/locales/en.json
```

Regels:
- nieuwe zichtbare tekst krijgt een translation key;
- NL en EN houden dezelfde keys;
- displaylabels en persistente opslagwaarden zijn verschillende concepten;
- bekende Planning-statussen/relaties mogen gelokaliseerd worden voor display;
- custom waarden blijven exact bewaard.

Een locale-wijziging mag geen boekdata wijzigen.

## 16. Modulekaart

### Startup/runtime
- `main.py` — Pythonversie + bootstrap
- `quietwriter/app.py` — QApplication, startup, smoke, MainWindow
- `quietwriter/startup.py` — startup helpers
- `quietwriter/runtime_profile.py` — prod/dev profiel
- `quietwriter/first_run.py`, `ui/first_run_wizard.py` — first run
- `quietwriter/crash_logging.py` — logging/notifier
- `quietwriter/workspace_path.py` — veilige werkmappaden

### Opslag/integriteit
- `storage.py` — Library/Book/chapters/archive/trash
- `revisions.py` — revisions en snapshots
- `integrity.py` — audit/herstel
- `migrations.py` — expliciete boekmigraties
- `field_merge.py` — drie-wegs merge helpers

### Editor
- `ui/editor_page.py`
- `ui/manuscript_editor.py`
- `manuscript_markup.py`
- `typography.py`
- `editor_view.py`
- `spell_engine.py`, `ui/spell_panel.py`
- `search.py`, `ui/search_panel.py`

### Planning
- `planning_models.py`
- `planning_storage.py`
- `planning_validation.py`
- `ui/planning/`
- `chapter_context.py`, `ui/chapter_context_panel.py`

### Publicatie/export
- `publication_models.py`
- `publication_storage.py`
- `ui/publication/`
- `exporting/`

### Media
- `media/`
- `ui/media_manager_page.py`
- `ui/image_block_card.py`
- `ui/image_insert_widget.py`

### AI Meelezer
- `ai/providers.py`
- `ai/ollama_provider.py`
- `ai/openrouter_provider.py`
- `ai/context.py`
- `ai/prompting.py`
- `ai/conversations.py`
- `ai/memory_suggestions.py`
- `ai/planning_context.py`
- `ai/quick_actions.py`
- `ai/ui.py`
- `persona_profile.py`, `book_profile.py`, `book_memory.py`

### UI/infrastructuur
- `ui/main_window.py`
- `ui/rail_model.py`
- `ui/current_page_stack.py`
- `ui/settings_page.py`
- `i18n.py`
- `themes.py`
- `icon_theme.py`
- `font_catalog.py`
- `dictionary_catalog.py`

## 17. Test- en reviewworkflow

Voor een wijziging is de minimale lokale volgorde:

```bash
python tools/check_undefined_names.py
pytest
pytest -m qt
```

`pytest -m qt` is de expliciete echte PySide6/Qt-runtime subset. Gebruik niet `-k qt` als maatstaf.

Voor een release:
- beide OS'en in CI;
- Windows portable build;
- executable `--smoke-test`;
- release hygiene;
- tag/versioncontrole.

## 18. Werken met een AI-code-reviewer

Een AI of externe ontwikkelaar hoort vóór wijzigingen minimaal te lezen:

1. `PROJECT_GUIDE.md`
2. `ARCHITECTURE_AND_DATA_SAFETY.md`
3. `PRODUCT_AND_UI_PHILOSOPHY.md`
4. `HISTORY_AND_LESSONS.md`
5. `TEST_STRATEGY.md`
6. dit document

Bij een concrete UI-wijziging ook `UI_REFERENCE.md`.

Review niet alleen source-inspection. De historische regressies laten zien dat Qt-signalen, timers, modaliteit, parenting, Undo en Windows-filehandles echte runtime nodig hebben.

## 19. Build

Windows:

```bat
build_exe.cmd
```

De build:
- maakt een clean allowlist-stage;
- haalt buildresources op;
- bouwt PyInstaller onedir;
- kopieert `LEESMIJ.txt` naast de EXE;
- controleert hygiene;
- maakt ZIP + SHA-256.

Voor alleen staging:

```bash
python tools/prepare_release.py
python tools/prepare_release.py --check
```

Tests kunnen via `QUIETWRITER_STAGE_DIR` een tijdelijke stage gebruiken zodat de bronmap na pytest schoon blijft.

## 20. Branding

Zie `../branding/README.md` en `RELEASE_BRANDING_AND_OPERATIONS.md`.

De generator vereist de devdependencies, waaronder `shapely`.

## 21. Belangrijkste valkuilen

- Qt-presentatie is geen manuscriptbron.
- Future format is geen corruptie.
- `parent()` is geen betrouwbare service locator.
- Een cache is niet autoritatief.
- Geen netwerkcall naar OpenRouter alleen door paneel openen.
- Een async AI-callback kan stale zijn na boekwissel.
- Een mislukte recovery mag lokale RAM-tekst niet laten verdwijnen.
- Windows filehandles expliciet sluiten.
- Gelokaliseerde labels niet direct opslaan als canonical data.
- Geen tweede mutatieroute voor hoofdstukvolgorde.
