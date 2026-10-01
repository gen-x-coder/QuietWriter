# Tussentijds rapport 0.34.7

## Doel
De eerder alleen zichtbare hoofdstukplanning gecontroleerd en transparant inzetbaar maken als AI-context, zonder het Planning-schema of de brondata te wijzigen.

## Implementatie
- Nieuwe QCheckBox **Planning van dit hoofdstuk gebruiken** in het AI-contextpaneel.
- Persistente voorkeur `ai_use_chapter_planning`, standaard `true`.
- `chapter_planning_preview()` blijft de enige bron voor de opgeslagen hoofdstukplanning.
- `send()` voegt alleen bij ingeschakelde én betrouwbare hoofdstukplanning de exacte previewtekst toe.
- `build_system_prompt()` heeft een aparte sectie `PLANNING VAN HET HUIDIGE HOOFDSTUK`; de bestaande `GESELECTEERDE PLANNINGCONTEXT` blijft apart.
- Op Boekenplank bepaalt `self.store` de interne boekstatus, zodat Planning-acties ook intern uit staan.

## Tests lokaal
- current: 183 geslaagd, 13 overgeslagen.
- current + legacy, exclusief twee bekende fontresource-tests: 605 geslaagd, 37 overgeslagen, 280 subtests geslaagd.
- Nieuwe niet-Qt prompttests bewaken scheiding tussen automatische hoofdstukplanning en handmatig geselecteerde Planning.
- Nieuwe Qt-test (voor Claude/lokale PySide6) bewaakt toggle aan/uit, exacte previewtekst en Boekenplank-begintoestand.
