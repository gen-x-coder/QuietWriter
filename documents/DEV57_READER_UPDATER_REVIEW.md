# QuietWriter 1.5.0-dev.57 — kwaliteitsronde en Claude-overdracht

## Basis en scope

Gebaseerd op dev.56. De OpenRouter-verbinding, modelselectie, browserauthenticatie en lokale geheugenopslag zijn ongewijzigd. De modelidentificatie bij `openrouter/free` maakt wisselende modellen per antwoord zichtbaar.

## Meelezer

De systeemprompt is aangescherpt voor **vervolgopdrachten om manuscripttekst te schrijven**. Ook na een eerdere afwijking van een ander model moet de Meelezer redactionele suggesties geven, niet zelf twee nieuwe fictieve alinea's produceren. Deze verbetering is een promptmaatregel, geen waterdichte outputvalidator. Bij `openrouter/free` kunnen modellen de rol nog steeds verschillend interpreteren.

Auteurscanon (zoals `Pip heeft geen haar`) hoeft niet letterlijk al in het manuscript te staan. De AI mag geen opslag in Boekgeheugen claimen. Handmatig **Onthouden** is de betrouwbare opslagroute met bevestiging en herleescontrole; modelgeproduceerde geheugenvoorstellen blijven aanvullend en kunnen uitblijven.

## Updater-pilot

De onvoltooide optie **Updates automatisch downloaden** is buiten de gewone instellingen verborgen. Alleen wanneer in de actieve boekenwerkmap een **leeg regulier bestand** `.quietwriter-update-pilot` bestaat, worden de proefinstelling en uitleg getoond. De downloadoptie blijft ook dan uitgeschakeld: er is geen werkende installatieroute. De bestaande handmatige/automatische controle op stabiele releases blijft voor iedereen beschikbaar. De eventuele proefknop in het updatebericht is eveneens afgeschermd via dezelfde gate.

## Uitgevoerde controles

- Test voor ontbrekende/lege/niet-lege pilotmarker en interfacegate.
- Opstartconstanten `APP_NAME`, `__version__`.
- Promptcontract voor schrijversrol, vervolgvragen, auteurscanon en opslagclaims.
- Bestaande gerichte Meelezer-, Boekgeheugen- en updater-gatetests.

## Openstaande praktijkvalidatie

1. Start Windows zonder marker: in Instellingen > Updates ontbreken zowel proefprogramma als automatische downloadproef, en bij updates ontbreekt de proefknop.
2. Maak een leeg `.quietwriter-update-pilot` bestand in de actieve boekenwerkmap, herstart: de proefinfo verschijnt; installeren kan niet. Verwijder bestand en herstart: alles verdwijnt weer.
3. Test dezelfde vragen met `openrouter/free` en één vast model. Vraag (a) oogkleur Pip, (b) nieuwe canon zonder manuscriptbewijs, (c) schrijf een openingsalinea, (d) schrijf twee vervolgalinea's, (e) onthoud dit. Controleer rolvastheid, brononderscheid, lokale opslagclaims en modelidentificatie.
4. Test handmatig Onthouden, herstart boek, controleer Boekgeheugen.

## Claude — gerichte onafhankelijke review (pas na Windows-validatie)

Review in één ronde: privacy en authenticatie (OpenRouter sleutelmethoden), OpenRouter-streaming en modelmetadata, betrouwbare opslag van Boekgeheugen, promptinjectierisico's vanuit manuscript/model, rolvastheid en streaming-outputguards, updater-pilot fail-closed, GUI-lifecycle (pop-out), regressietestdekking. Meld bevindingen op prioriteit met concrete bestandslocatie en reproduceerbare stappen. Maak géén wijzigingen zonder overleg; vermijd breed herontwerp. Gebruik de andere kernstukken in `documents/` en de huidige broncode als uitgangspunt.
