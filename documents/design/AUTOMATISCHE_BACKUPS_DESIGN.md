# QuietWriter 1.4 — ontwerp automatische boekback-ups

Status: back-upkern beschikbaar sinds 1.4.0-dev.3; automatische planning en UI nog niet geïmplementeerd.

## Doel

Bescherm het boek tegen verlies van de volledige werkmap of geschiedenis, zonder de schrijver tijdens het schrijven te onderbreken. Versiegeschiedenis blijft bestaan en back-ups vormen geen tweede actieve boekbron.

## Gedrag voor de schrijver

- Instellingen > Algemeen > Back-ups: `Automatische back-ups maken` (bij eerste ingebruikname uit totdat een geschikte locatie bevestigd is), `Back-upmap`, `Nu een back-up maken`, `Back-ups bewaren` en een rustige status van de laatste succesvolle back-up.
- De schrijver kiest een map **buiten** de actieve werkmap. QuietWriter raadt aan een andere schijf of onafhankelijke opslag te kiezen. Een map op dezelfde schijf is toegestaan na een duidelijke toelichting dat dit niet tegen schijffalen beschermt.
- Automatische back-up: bij het veilig sluiten of verlaten van een gewijzigd boek, hooguit eenmaal per lokale kalenderdag per boek. Geen terugkerende timer tijdens het typen. Niet blokkeren op het afsluiten van het venster.
- Handmatige back-up: expliciet knopje, ook als er die dag al een back-up gemaakt is. Bij geen wijzigingen melden dat de laatste kopie actueel is; optioneel expliciet nieuwe kopie forceren pas als de UX dat vraagt.
- Rustige melding bij een fout; schrijven en normaal opgeslagen manuscript blijven beschikbaar. Geen modal op een gewone automatische fout.
- Back-ups openen we niet als live boeken. Herstel loopt via bestaande import; die weigert momenteel een al bestaande boekidentiteit. Herstel als aparte kopie vereist nog een expliciet ontworpen optie; bestaand werk wordt nooit stil overschreven.

## Technische bron en inhoud

- Gebruik `quietwriter.qwbook_io.export_qwbook(library, book, destination, include_history=True, include_ai_chat=True)` en de bestaande importvalidatie. Geen eigen tweede archiefformaat.
- Een privéback-up omvat het volledige huidige boek inclusief media, Planning, boekgegevens en History; Meelezer-gesprek wordt standaard meegenomen omdat dit privéherstel betreft. Communiceer dit expliciet bij de mapkeuze, zeker bij gedeelde schijven. De gewone overdrachtsexport behoudt zijn bestaande privacykeuzes.
- Lees uitsluitend een schoon opgeslagen en door `library.verify_book_unchanged(book)` gevalideerde toestand. Geen export vanaf dirty editorbuffers of wanneer een opslaan/conflict nog open staat.
- Een export schrijft naar een tijdelijk bestand in de doelmap en promoveert via de bestaande atomische replace. De automatische taak krijgt een unieke bestandsnaam; bestaande back-ups worden nooit doelwit van overwrite.
- Bronbestanden kunnen onder OneDrive of externe sync veranderen; bij wijziging tijdens export afbreken, geen onvolledige back-up publiceren en later opnieuw proberen.

## Planning en gelijktijdigheid

- Start vanuit de bestaande veilige boekwissel-/afsluitroute **na succesvolle save**. De UI mag de export niet op de Qt-hoofdthread uitvoeren. Een zware export krijgt een worker met expliciet beheerde levensduur.
- Bij daadwerkelijk afsluiten mag de app de worker niet heimelijk afbreken of zichzelf ophouden zonder gebruikerskeuze. In de implementatiefase expliciet bepalen: export vóór afsluiten op niet-blokkerend gekozen moment, of een zelfstandig veilig voltooiende job. Een onafgemaakte export mag nooit als geslaagd worden geregistreerd.
- Eén back-upjob per boek tegelijk, plus een begrensde werkqueue. Boekwissel, afsluiten, herstart en sleep/resume zijn afzonderlijke integratietests.
- Tijdens worker-export worden mutaties van live bronbestanden niet geblokkeerd; de bestaande stabiele-byte- en revisioncontroles bepalen of een snapshot betrouwbaar is. Bij conflict afbreken en opnieuw plannen.

## Wijzigingsdetectie en status

- Sla per boek-ID de laatste geslaagde back-up vast, inclusief lokale dag, contentfingerprint en bestandsnaam, in *apparaatlokale instellingen buiten de boekmap*. Dit is slechts een optimalisatie, nooit autoritatief.
- Fingerprint moet het werkelijk meegenomen pakket weerspiegelen (huidig boek plus History indien meegenomen). Alleen `book.json` mtime of een hoofdstukdatum is onvoldoende.
- Bij ontbrekende/onleesbare status niet concluderen dat een back-up veilig bestaat: controleer in de eigen back-upmap of maak een nieuwe.
- Schrijf successtatus pas nadat het volledige archief bestaat en basiscontrole van formaat/manifest en veilige leesbaarheid geslaagd is; integriteitsvalidatie van de inhoud moet door tests aantoonbaar zijn.

## Bestandsnamen, grenzen en retentie

- Isolatie per boekidentiteit: `<back-upmap>/QuietWriter/<book-id>/` (geen door de gebruiker veranderbare titel als primaire sleutel). Bijvoorbeeld `2026-10-08_2034_<unieke-suffix>.qwbook`.
- Beperk retentie tot de **eigen** QuietWriter-back-upmap en uitsluitend herkende, door de app geregistreerde bestanden van hetzelfde boek. Volg geen symlinks of junctions; wis nooit onbekende bestanden.
- Startvoorstel: 7 dagelijkse en 4 wekelijkse herstelpunten. Een handmatige back-up wordt **niet** automatisch opgeruimd zonder aparte expliciete afspraak/markering.
- Retentie pas na een nieuw, aantoonbaar geslaagd archief. Fout bij opruimen is niet fataal; nooit de laatste geslaagde back-up verwijderen.
- Het moment van back-up en retentie wordt berekend met lokale kalenderdagen, maar bestandsnamen bevatten een unieke component om botsingen bij zomer-/wintertijd en meerdere apparaten te voorkomen.

## Grenzen en veiligheid

- Weiger de werkmap zelf, iedere bovenliggende map van de werkmap en iedere submap daarvan als back-updoel: geen recursieve export of onbedoeld wissen.
- Controleer symlinks/junctions, schijfvol, rechten, onderbroken opslag, Windows-locks, ongeldige archieven en bestandssynchronisatie.
- Geen geheime credentials of manuscriptinhoud in logbestanden. Foutmeldingen aan de schrijver zijn begrijpelijk en noemen een handelbare vervolgstap.
- `library.json` blijft leidend voor de Boekenkast. Back-upindex en status mogen nooit boeken automatisch zichtbaar maken.
- Voer geen wijziging uit aan bestaand `.qwbook`-formaat of bestaande importsemantiek zonder een apart compatibiliteitsbesluit.

## Testplan voor de eerste werkende iteratie

1. Nieuw boek, back-upmap gekozen, automatische back-up aan: eerste veilige sluiting levert één `.qwbook`; bestaande import maakt als kopie een boek met nieuwe identiteit.
2. Boek onveranderd opnieuw openen/sluiten: geen tweede automatische kopie.
3. Eén hoofdstuk wijzigen en sluiten op dezelfde dag: maximaal één automatische kopie per dag; op volgende dag weer één.
4. Handmatig `Nu een back-up maken`: controleer de begrijpelijke status en of de inhoud werkelijk importeerbaar is.
5. Een kunstmatig onleesbare map, schijfvol en een Windows-locked doel: geen dataverlies, geen hang, geen half archief als geslaagd.
6. Simuleer een verandering van de bron tijdens export: mislukte poging laat bestaande goede back-ups ongemoeid.
7. Controleer 7+4-retentie, handmatige kopieën, symlinks/junctions, vreemde bestanden en laatste resterende back-up.
8. Test echte UI op Windows, ook op een tragere laptop en bij OneDrive-synchronisatie; geen typing-lag of vertraagd sluiten.
9. Controleer vertalingen voor alle vijf talen en zorg dat de interface niet technisch klinkt.

## Eerst nog uit te werken vóór productcode

- Lifecyclebesluit voor het afsluiten van de app terwijl een achtergrond-export loopt, met expliciete, reproduceerbare Windows-tests.
- Implementatie van betrouwbare, goedkope fingerprint zonder de UI te blokkeren en zonder race tussen fingerprint en export.
- Exacte configuratie- en migratievelden en UI-locatie, mede op basis van de bestaande `QSettings`-patronen.
- Beschikbaarheid en herstelbeleid bij wisselende back-upmedia (USB/netwerkschijf) zonder onbedoelde lokale fallback.

Dit document is de ontwerpgrens voor 1.4. De publieke 1.3-prerelease en beide README-bestanden worden niet gewijzigd.
