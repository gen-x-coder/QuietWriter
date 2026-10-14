# Dev.50 — OpenRouter-modelselectie

De keuze **Geschikt voor schrijven / Alle modellen** blijft gelijk.

- De vorige beschrijvingsfilter sloot algemene modellen zoals Claude en Gemini ten onrechte uit omdat hun beschrijving programmeervaardigheid noemde.
- De nieuwe filter sluit alleen ondubbelzinnige codefamilies op basis van model-ID uit, waaronder `coder`, `codex`, `codestral`, `devstral`, `code`, Poolside en Grok Build.
- Voor de schrijfweergave gebruikt QuietWriter de `architecture.output_modalities` uit de OpenRouter-catalogus. Modellen waarvan expliciet bekend is dat ze **geen tekst** kunnen uitvoeren, worden verborgen. Ontbrekende modaliteitsinformatie is geen reden voor uitsluiting.
- `openrouter/free` blijft altijd beschikbaar.
- De instelling **Alle modellen** toont ook uitgesloten specialisten. Bestaande credentials en authenticatie zijn ongewijzigd.

De analyse van de eerdere offline audit leverde 22 codespecialisten op, exclusief modellen die geen tekst kunnen uitvoeren. Het precieze aantal na verversen hangt af van de actuele OpenRouter-catalogus.
