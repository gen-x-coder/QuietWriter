# QuietWriter 1.0.0-rc5

RC5 is een kleine release-candidatehardening bovenop RC4. De functieset blijft bevroren.

## Opgelost

- Een beschadigde globale `persona/schrijver.md` legt QuietWriter niet meer stil tijdens het opstarten. De persona-pagina opent in een duidelijke alleen-lezen toestand en het bronbestand wordt niet overschreven.
- De Meelezer behandelt beschadigde optionele contextbronnen fail-open: Schrijverspersona, Boekprofiel en Boekgeheugen worden afzonderlijk overgeslagen wanneer zij niet als UTF-8 gelezen kunnen worden.
- In de contextinformatie wordt zichtbaar gemaakt welke bron wegens beschadiging niet is meegestuurd.

## Niet veranderd

- Geen nieuwe v2-functionaliteit.
- Darlings blijft uitsluitend ontwerp totdat stabiele 1.0.0 is uitgebracht.
- De bestaande conflict-, History- en corruptiebescherming voor auteursdata blijft leidend.

## Nog te valideren

Voor de 1.0-tag blijven de praktische Windows-/provider-/grote-boekchecks uit `ROADMAP_AND_IDEAS.md` van toepassing.
