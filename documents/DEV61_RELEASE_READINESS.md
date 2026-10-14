# QuietWriter 1.5.0-dev.61 — releasevoorbereiding

## Stand

- De Windows-praktijktest van dev.60 met Boekgeheugen en OpenRouter Free is door de gebruiker goedgekeurd.
- De gerichte OpenRouter-tests zijn lokaal uitgevoerd. De complete Qt-testsuite en Windows-EXE zijn niet in deze Linux-omgeving gevalideerd: PySide6 ontbreekt.
- OpenRouter API-verzoeken accepteren alleen `https://openrouter.ai/api/v1` als basis-URL; een afwijkende registry/QSettings-waarde wordt expliciet geweigerd.
- Bewuste beperking: annuleren tijdens het wachten op HTTP-headers kan niet direct worden afgebroken; connect-timeout is 10 seconden, read-timeout 45 seconden. Verder valideren op Windows en bij haperend netwerk.
- Modelkeuze `openrouter/free` is per verzoek; het gekozen model wordt bij een antwoord getoond. Sommige modellen zijn ongeschikt voor schrijfadvies. Geen heuristische retry of inhoudelijke filtering toegevoegd.

## Nog af te vinken voordat publicatie start

1. Volledige pytest-suite met PySide6 in offscreen en normaal Windows, inclusief Claire/Claude-regressieharnassen (waar relevant).
2. `python main.py --smoke-test` moet zonder gebruikersinteractie afsluiten met rc 0.
3. Windows-praktijkcontrole: opstarten, Boekgeheugen bewaren/heropenen, Meelezer-pop-out, OpenRouter browserlogin en handmatig, veilige HTTPS-linkbevestiging, pilot-gate afwezig.
4. Controleer releasebron en git-diffs tegen de twee repositories. Push geen ongeteste of onbedoelde bestanden.
5. GitHub-volgorde: (a) `quietwriter-dev`, (b) `quietwriter`, (c) Windows Actions **alleen** op `quietwriter`, (d) buildartifact + exe controleren, (e) nieuwe GitHub **pre-release** met bijbehorende releasenotes en geverifieerde portable EXE.

Er is niets gepusht, gebouwd of gepubliceerd in deze iteratie.
