# QuietWriter — publieke positionering en GitHub-presentatie

Dit document legt de productstem en publieke presentatie van QuietWriter vast. Het is bedoeld als bron voor README's, website, GitHub About en toekomstige releasecommunicatie.

## Kernpositionering

**Rustig schrijven. Eerlijk meelezen.**

Ondersteunende gedachte:

**Alles wat je nodig hebt om je boek af te maken. Zonder dat de software het probeert over te nemen.**

De centrale productregel is:

**Blijf schrijven.**

QuietWriter moet de schrijver zo weinig mogelijk uit het schrijfritme halen. Nieuwe functies zijn alleen waardevol als ze schrijven, plannen, reviseren of afronden merkbaar beter maken.

## Productkarakter

QuietWriter is:

- lokaal en van de gebruiker;
- rustig en voorspelbaar;
- anti-bloat;
- tekstgericht;
- meertalig;
- open source onder GPLv3;
- zonder verplicht account of abonnement;
- terughoudend met automatisering.

QuietWriter probeert geen alles-in-één worldbuilding-, DTP- of cloudplatform te worden.

Twee zinnen die de gewenste toon goed samenvatten:

> QuietWriter hoeft niet alles te kunnen. Dat is geen ontbrekende feature.

> Meer knoppen is makkelijk. Minder software voelen is moeilijker.

## AI-positionering

De AI-functionaliteit heet in het Nederlands **AI Meelezer** en in het Engels **AI Reader**.

De Meelezer:

- mag analyseren;
- mag feedback geven;
- mag inconsistenties zoeken;
- mag feiten controleren;
- mag rekening houden met boekcontext, persona, profiel en geheugen;
- mag het manuscript niet zelfstandig schrijven of herschrijven.

AI blijft optioneel. Met Ollama kan de Meelezer lokaal draaien. Bij externe providers wordt context pas verstuurd na een bewuste gebruikersactie.

## Lokale positionering

De basisboodschap blijft:

- geen verplichte cloud;
- geen account nodig;
- manuscript en projectdata blijven lokaal;
- gebruiker houdt zelf controle over bestanden en back-ups.

De humane toon mag droog zijn. Voorbeeld:

> Waar staat mijn boek? Op jouw computer. Dat klinkt misschien weinig revolutionair. We zijn er toch behoorlijk enthousiast over.

## Nederlandse en Engelse README

De standaard README is Nederlands:

- `README.md`

De Engelse versie is:

- `README_EN.md`

Bovenaan Nederlands:

`**Nederlands** · [English](README_EN.md)`

Bovenaan Engels:

`[Nederlands](README.md) · **English**`

Algemene metadata noemt geen vast aantal ondersteunde talen. Gebruik:

- **Meertalig**
- **Multilingual**

Huidige hero-regels:

- Nederlands: `Lokaal · Windows · Meertalig · 15 thema's`
- Engels: `Local · Windows · Multilingual · 15 themes`

De Engelse README is geen letterlijke vertaling; toon en humor blijven behouden.

## Productscreenshots

Publieke productscreenshots staan onder `branding/screenshots/`.

Canonieke set:

- `hero-met-logo.png`
- `02-open-punten.png`
- `03-meelezer.png`
- `04-in-dit-hoofdstuk.png`
- `05-planning-personages.png`
- `07-bewaarplaats.png`
- `08-versiegeschiedenis.png`
- `11-exporteren.png`
- `13-themas.png`

Gebruik screenshots om productgedrag te tonen, niet om ieder bestaand scherm te documenteren.

## GitHub About-description

Doeltekst:

> QuietWriter — a calm, local writing app for books. Plan, write, revise and export without accounts or subscriptions. Multilingual and open source.

GitHub About-metadata kan buiten de bronrepository worden aangepast en moet daarom periodiek handmatig worden gecontroleerd.

## GitHub topics

Gewenste topics:

```text
writing
writing-app
novel-writing
book-writing
creative-writing
author-tools
writers
manuscript
desktop-app
offline-first
local-first
privacy
open-source
multilingual
python
pyside6
epub
ollama
openrouter
ai-assistant
```

Gebruik bewust geen positionering als `scrivener-alternative`; QuietWriter wordt op eigen kwaliteiten gepresenteerd.

## Huidige 1.2-productstaat

In de actieve 1.2-lijn zijn onder andere aanwezig:

- Open punten/placeholders;
- Darlings/bewaarplaats;
- Planning;
- In dit hoofdstuk;
- personages;
- hoofdstukken en scènes;
- versiegeschiedenis/herstel;
- AI Meelezer;
- Boekprofiel en Boekgeheugen;
- spelling;
- zoeken;
- focusweergave;
- opmaakbalk;
- thema's;
- import/export;
- lokale opslag.

Schrijfdoelen en voortgang zijn nog gepland.

## Belangrijk verschil tussen publieke presentatie en releasebron

De publieke README kan tijdens actieve ontwikkeling al de actuele productrichting tonen, maar officiële releaseclaims moeten overeenkomen met de werkelijk gepubliceerde release.

Op 6 oktober 2026 is de publieke technische bronbaseline nog `1.1.0`, terwijl actieve 1.2.x-ontwikkeling lokaal/private plaatsvindt. Vóór de volgende release moet de volledige geteste 1.2-bron naar de publieke repository worden gepromoveerd en door publieke CI worden gevalideerd.

## Behoud bij toekomstige herschrijvingen

Bij toekomstige README-, website- of release-teksten moeten deze principes behouden blijven:

1. Blijf schrijven.
2. AI is Meelezer, geen schrijver.
3. Lokaal en van jou.
4. Anti-bloat.
5. Rust boven feature density.
6. Meertalig zonder onnodig één taal als hoofdbeperking te presenteren.
7. Humor mag, maar productclaims moeten controleerbaar blijven.
