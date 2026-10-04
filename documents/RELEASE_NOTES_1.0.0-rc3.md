# QuietWriter 1.0.0-rc3

RC3 is een kleine dataveiligheidsrelease bovenop de functioneel bevroren RC2.

## Belangrijkste wijziging

- Schrijverspersona gebruikt nu optimistic concurrency. Een wijziging van `persona/schrijver.md` door een andere computer wordt vóór Opslaan gedetecteerd en nooit stil overschreven.
- Bij een conflict kan de gebruiker zijn lokale versie of de versie op schijf kiezen. De versie die anders verloren zou gaan wordt eerst als herstelkopie onder `archive/persona/` opgeslagen.
- De globale persona gebruikt bewust een eigen herstelmap omdat hij niet bij één boek hoort en dus niet in de per-boek Versiegeschiedenis past.

## Bewuste uitzondering

`.quietwriter/ai_chat.json` is een optioneel Meelezer-gesprekslog. Voor 1.0 blijft dit bestand last-writer-wins bij gelijktijdig gebruik op twee computers. Het is geen manuscript-, Planning-, Boekprofiel- of Boekgeheugenbron.

## Scope

Geen nieuwe v2-functionaliteit. Darlings mag worden ontworpen, maar wordt pas na stabiele 1.0.0 geïmplementeerd.
