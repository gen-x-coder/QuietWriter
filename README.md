# QuietWriter

QuietWriter is een Nederlandstalige Windows-schrijfomgeving voor langere teksten en boeken. Je schrijft in hoofdstukken, plant personages en scènes, controleert spelling en exporteert onder meer naar EPUB en PDF. Alles draait op je eigen computer, zonder account of abonnement.

QuietWriter bevat daarnaast een optionele **AI Meelezer** voor feedback, consistentie, feiten en stijl-/personacontrole. De Meelezer is bedoeld als tweede lezer, niet als co-auteur of tekstgenerator.

## Download

De nieuwste **stabiele** Windows-versie is na de eerste definitieve release altijd beschikbaar via:

**[QuietWriter voor Windows downloaden](https://github.com/gen-x-coder/QuietWriter/releases/latest/download/QuietWriter-windows-portable.zip)**

Pak de ZIP volledig uit voordat je QuietWriter start.

> Zolang alleen een release candidate beschikbaar is, gebruik je de betreffende testversie onder **Releases**. Een prerelease wordt bewust niet door de vaste `latest`-downloadlink gebruikt.

## Release candidates

Versies zoals `1.0.0-rc1` zijn testversies voor een kleine testgroep. Ze staan bij **Releases** met het label *Pre-release*.

## Windows SmartScreen

QuietWriter is op dit moment nog niet digitaal ondertekend. Windows SmartScreen kan daarom bij de eerste start een waarschuwing tonen. Kies in dat geval **Meer info** en daarna **Toch uitvoeren**, mits je QuietWriter via deze officiële repository hebt gedownload.

## Privacy en AI

QuietWriter is ontworpen als lokale schrijfapp. Je boeken en werkbestanden blijven lokaal.

De AI Meelezer is optioneel:

- met **Ollama** kan AI volledig lokaal draaien;
- met een externe provider zoals **OpenRouter** verlaat alleen context de computer wanneer je bewust een vraag aan de Meelezer stelt;
- het openen van de Meelezer verstuurt niet automatisch manuscripttekst.

## Releases en integriteit

Officiële Windows-downloads worden automatisch gebouwd vanuit de private ontwikkelrepository. Iedere release bevat naast de ZIP een SHA-256-controlebestand:

`QuietWriter-windows-portable.zip.sha256`

## Broncode

Deze publieke repository bevat bewust **geen broncode**. De ontwikkelrepository is privé.

## Licentie

QuietWriter is geen open-sourceproject. De software is auteursrechtelijk beschermd. Componenten van derden vallen onder hun eigen licenties; die worden met de distributie meegeleverd.
