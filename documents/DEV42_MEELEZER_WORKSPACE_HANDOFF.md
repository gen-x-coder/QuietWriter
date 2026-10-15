# QuietWriter — AI Meelezer werkruimte (ontwikkelkandidaat)

## Goedgekeurd functioneel ontwerp

- Het bestaande rechterpaneel blijft de basis.
- 'Ruime werkruimte' verplaatst **dezelfde** AIPanel tijdelijk naar een groot venster en herstelt het paneel bij sluiten.
- Het actieve gesprek wordt niet automatisch opgeslagen, ook niet bij een AI-fout, warm-up of boekwissel.
- 'Gesprek bewaren' maakt een onveranderlijke JSON-snapshot per boek in `.quietwriter/saved_ai_conversations/`.
- Bewaarde gesprekken zijn alleen-lezen, en kunnen worden geëxporteerd naar Markdown/tekst.
- De geselecteerde passage wordt bij een gestelde vraag in de gesprekscontext bewaard als momentopname.
- AI-boekgeheugen en manuscript worden niet automatisch door chatopslag gewijzigd.
- Herkenbare aanbiederfouten worden begrijpelijker weergegeven; diagnostische details blijven beschikbaar.
- De bestaande provider- en prompt-hardening is niet aangepast.

## Technische opmerkingen / nog controleren

- De oude `ai_chat.json` van gebruikers blijft op schijf staan, maar wordt niet automatisch in het nieuwe handmatige archief geladen of verwijderd. Een eventuele eenmalige migratie vereist een expliciet ontwerpbesluit.
- Het vergrote venster gebruikt dezelfde Qt-widget, geen tweede worker. Visuele Windows-tests en tests tijdens een lopende aanvraag zijn nog nodig.
- Archief en export moeten worden getest met echte bestanden, boekimport/export, multi-book-switch en backups.
- Alle foutcategorieën zijn heuristisch op de beschikbare fouttekst gebaseerd; een meer betrouwbare providerstatusstructuur kan later volgen.
- De technische details staan nu onder de begrijpelijke melding, niet achter een afzonderlijke uitklapknop: dit UI-detail is nog niet conform het volledige ontwerp.
- De volledige testsuite is niet gedraaid. Alleen gerichte Python-tests waren beschikbaar; PySide6 is hier niet geïnstalleerd.
- Interne appversie ongewijzigd: dit is een broncode-reviewkandidaat, geen release.

## Windows-visuele test

1. Open een boek en de Meelezer rechts. Vraag om feedback, klik 'Ruime werkruimte'; controleer dat gesprek en invoer hetzelfde blijven.
2. Sluit de ruime werkruimte: het rechterpaneel komt terug, zonder tweede sessie.
3. Stel een vraag over geselecteerde tekst, bewaar het gesprek en open het via 'Bewaarde gesprekken'. Controleer de passage en export.
4. Sluit een niet-bewaard gesprek, open het boek opnieuw: het gesprek mag niet terugkomen.
5. Controleer Engelse/Nederlandse tekst, donkere thema's, een lang AI-antwoord en de foutmelding `Provider returned error`.
6. Controleer dat de Meelezer nog steeds geen code of recepten produceert indien dat buiten de rol valt, conform de bestaande gebruikers-hardeningstest.
