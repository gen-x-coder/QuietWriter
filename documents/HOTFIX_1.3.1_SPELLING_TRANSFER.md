# 1.3.1 spelling-hotfix -> 1.4 overdracht

Deze notitie voorkomt dat de 1.3.1-spellingsfix verloren gaat terwijl de actieve 1.4-lijn al verder is ontwikkeld.

## Root cause in 1.3.0

Het probleem bleek geen gewone crash te zijn maar een blokkade van de GUI-thread in `spylls.suggest()`.

Bij lange onbekende woorden kan de pure-Python Hunspell-implementatie zeer veel edit-kandidaten genereren. Vooral MAP-permutaties en compoundchecks in het Nederlandse OpenTaal-woordenboek kunnen daardoor exponentieel oplopen. Het spellingpaneel berekende suggesties synchroon en kon zo minutenlang niet reageren.

Alleen terugvallen op een ander woordenboek is geen echte oplossing: ONLYOFFICE maakt het probleem minder waarschijnlijk, maar niet onmogelijk.

## Wat 1.3.1 doet

### `quietwriter/spell_engine.py`

- `SUGGEST_BUDGET_SECONDS = 1.0`;
- na het laden van een Hunspell-dictionary wordt `dictionary.suggester.edits` per instantie omwikkeld;
- zodra de deadline is verstreken, worden geen nieuwe dure edit-kandidaten meer geproduceerd;
- daarna kan spylls zijn snellere ngram-fase vervolgen;
- gewone `known()`-lookups worden niet begrensd of vertraagd;
- de deadline wordt in `finally` altijd teruggezet.

### Woordenboekkeuze

De eerder gemaakte 1.3.1-keuze blijft behouden:

- meerdere dictionary providers per locale;
- persisted `spell_dictionary_source`;
- selector in Instellingen > Spelling;
- veilige fallback als de gekozen bron verdwijnt.

### Regressietest

`tests/current/test_spell_suggest_budget_131.py` gebruikt een klein synthetisch woordenboek met MAP-regels.

De test controleert:
- een pathologisch lang onbekend woord blijft binnen een redelijke tijd;
- normale correcties blijven beschikbaar;
- de deadline lekt niet naar volgende aanvragen.

## Naar 1.4 overnemen

Niet blind bestanden kopiëren; 1.4 kan inmiddels sterk zijn gewijzigd.

Neem semantisch over:

1. het suggestiebudget uit `spell_engine.py`;
2. de regressietest voor pathologische MAP-woorden;
3. meerdere dictionary providers per locale;
4. persisted `spell_dictionary_source`;
5. bronselector + veilige runtimefallback;
6. locale keys.

Daarna in 1.4 ook de vervolgstap uitvoeren die voor 1.3.1 bewust niet nodig is: suggesties buiten de GUI-thread berekenen, zodat zelfs een begrensde suggestieronde de interface niet kort blokkeert.

## Test na overname

- volledige testsuite;
- Qt runtime suite;
- Windows portable build;
- Meegeleverd én ONLYOFFICE;
- testwoorden `Aaaaaaaaaaaaaaaaaaaa`, `Aurelianus` en een normale fout zoals `bannaan`;
- spellingspaneel openen en Negeren doorklikken;
- bestaande gebruiker zonder `spell_dictionary_source` behoudt een bruikbare fallback.
