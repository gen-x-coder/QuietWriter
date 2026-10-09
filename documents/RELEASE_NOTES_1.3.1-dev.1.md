# QuietWriter 1.3.1-dev.1 — woordenboeken mogen kiezen

Deze hotfix-devbuild richt zich op één concrete 1.3.0-melding: spellingscontrole kan op een ander systeem vastlopen of crashen terwijl daar het meegeleverde Nederlandse Hunspell-woordenboek actief is.

De precieze oorzaak van die crash is nog niet bewezen. Daarom verandert deze build niet stil het standaardwoordenboek, maar maakt hij zichtbaar **welk woordenboek** wordt gebruikt en laat hij de schrijver wisselen tussen de gevonden bronnen voor dezelfde taal.

## Nieuw in deze devbuild

- Instellingen > Spelling heeft naast **Taal** nu ook **Woordenboek**.
- Voor dezelfde taal blijven meerdere gevonden bronnen beschikbaar in plaats van dat QuietWriter er vooraf één wegfiltert.
- Ondersteunde bronnen blijven: Meegeleverd, ONLYOFFICE, LibreOffice, OpenOffice en zelf toegevoegd via QuietWriter.
- De gekozen bron wordt lokaal in de programma-instellingen opgeslagen.
- Verdwijnt die bron later van de computer, dan valt QuietWriter veilig terug op een ander gevonden woordenboek voor dezelfde taal.
- De bestaande detailregel blijft het daadwerkelijke pad en .aff-gebruik tonen, zodat we bij dit incident precies kunnen zien welke woordenboekbestanden actief zijn.

## Bewust niet in deze build

Microsoft Word/Office gebruikt niet hetzelfde openbare Hunspell-model als de bronnen hierboven. QuietWriter doet daarom niet alsof het volledige Microsoft Office-spellingswoordenboek kan worden gebruikt. Zelf toegevoegde compatibele .dic/.aff-bestanden blijven wel ondersteund.

Deze build is bedoeld om de gemelde 1.3.0-spellingscrash reproduceerbaar te onderzoeken en, indien een andere woordenboekbron stabiel blijkt, direct een bruikbare uitweg te bieden.
