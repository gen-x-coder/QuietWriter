# Tussentijds rapport 0.32.0

## Aanleiding

Na reviewronde 25 is 0.31.6 volledig groen. De laatste stabiliteitsrandgevallen zijn gesloten. De eerste volgende roadmapstap is daarom UI/editor polish, met vier concrete punten uit praktijkgebruik en Claude's laatste observatie.

## Besluiten

### AI is één zichtbare productfunctie

Wanneer `ai_enabled=false` zijn AI-assistent, Schrijverspersona, Boekprofiel en Boekgeheugen niet zichtbaar. De pagina-objecten en Markdownbestanden blijven bestaan. Opnieuw inschakelen herstelt de UI zonder migratie of dataverlies.

### Geavanceerde opties zijn visibility-only

Nieuwe setting `advanced_options`, default `True`. In 0.32.0 bepaalt deze uitsluitend Integriteit & herstel. De architectuur is bewust generiek genoeg voor latere specialistische opties, maar er worden nu geen andere functies onder gehangen.

### Spelling uit is onmiddellijk uit

`load_dictionary_from_settings()` deactiveert de highlighter, forceert `rehighlight`, markeert de QTextDocument-presentatie dirty en vraagt de viewport opnieuw te tekenen. Het spellingspaneel wordt bij uitschakelen gesloten en de toolknop verborgen.

### Herstel wordt transparanter, niet anders

`BookIntegrityChecker.latest_recovery_candidate()` exposeert naast het pad ook `kind`, `created_at` en versie-id. `latest_recovery_file()` blijft compatibel. Integriteit toont die provenance; selectie en restorelogica blijven ongewijzigd.

## Roadmap

- 0.32.x: concrete UI/editor polish en runtimebevindingen.
- 0.33: informatiearchitectuur en definitieve AI/persona-positionering.
- 0.34: Planning tijdens het schrijven, te beginnen met “In dit hoofdstuk”.

## Lokale tests

Volledige suite in deze omgeving: 556 passed, 27 skipped, 280 subtests. Alleen de twee bekende fontresource-tests falen omdat `resources/fonts/font_manifest.json` niet in deze sandbox-build aanwezig is.

Nieuwe/gerichte 0.32-tests: AI-visibility, geavanceerde opties, spelling-refresh en recovery provenance zijn groen. Echte Qt/PySide6-weergave laat ik expliciet door Claude testen.
