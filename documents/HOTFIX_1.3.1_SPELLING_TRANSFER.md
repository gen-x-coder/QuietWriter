# 1.3.1 spelling-hotfix -> 1.4 overdracht

Deze notitie voorkomt dat de 1.3.1-spellingsfix verloren gaat wanneer de actieve 1.4-lijn verder is ontwikkeld.

## Waarom deze patchlijn apart bestaat

QuietWriter 1.3.0 is publiek uitgebracht. Tijdens gebruik op een andere Windows-computer is gemeld dat de spellingscontrole blijft hangen en daarna crasht. Op screenshots gebruikt dat systeem het **Meegeleverd** Nederlandse woordenboek. Op Lucas' eigen systeem wordt normaal het gevonden ONLYOFFICE-woordenboek gebruikt.

De exacte crashoorzaak is nog niet vastgesteld. De 1.3.1-patchlijn voegt daarom eerst expliciete woordenboekbronkeuze toe, zodat dezelfde installatie kan worden getest met Meegeleverd, ONLYOFFICE, LibreOffice, OpenOffice of een zelf toegevoegd compatibel Hunspell-woordenboek.

## Patcharchitectuur

Belangrijkste wijzigingen:

- quietwriter/dictionary_catalog.py
  - bewaart meerdere dictionary entries met hetzelfde locale;
  - entries(locale) kan alle bronnen voor één taal teruggeven;
  - get(locale, source) respecteert een expliciete bronkeuze en valt veilig terug als die bron ontbreekt.

- quietwriter/ui/settings_page.py
  - voegt spell_dictionary_source toe naast spell_language;
  - bewaart instelling spell_dictionary_source;
  - toont alleen bronnen die voor de gekozen taal werkelijk zijn gevonden.

- quietwriter/ui/editor_page.py
  - laadt bij spellingscontrole de gekozen bron;
  - oude installaties zonder broninstelling behouden het bestaande voorkeursgedrag.

- locales
  - vier nieuwe spellingstrings in alle vijf talen.

- tests
  - regressietests voor meerdere bronnen per locale, fallback en instelling/runtime-contract.

## Naar 1.4 overnemen

Niet blind hele bestanden kopiëren: 1.4 kan inmiddels sterk zijn gewijzigd.

Neem semantisch over:
1. meerdere dictionary providers per locale in de catalogus;
2. persisted spell_dictionary_source;
3. bronselector in Spelling;
4. runtime selection + veilige fallback;
5. locale keys;
6. regressietests aangepast aan de 1.4-architectuur.

Na overname in 1.4:
- volledige testsuite;
- Qt runtime suite;
- Windows-test met Meegeleverd én ONLYOFFICE;
- controleren dat bestaande gebruikers zonder de nieuwe setting hetzelfde woordenboek krijgen als vóór de hotfix.

## Nog te onderzoeken

Deze wijziging bewijst niet waarom het meegeleverde Nederlandse woordenboek op het gemelde systeem vastloopt/crasht. Voor een echte root-cause analyse zijn crashlog, exacte handeling en liefst reproduceerbare tekst/systeeminformatie nodig. De bronselector is zowel een diagnostisch hulpmiddel als een gebruikersvriendelijke fallback.
