# QuietWriter 1.3.1 — lange woorden mogen weer gewoon raar zijn

QuietWriter 1.3.1 is een kleine hotfix met een heel specifiek talent:

**Hou je van lange woorden die niet bestaan? Dan loopt QuietWriter daar niet meer op vast.**

Dat klinkt misschien als een nicheprobleem, totdat één fantasienaam, samengestelde typefout of enthousiaste rij klinkers besluit dat de spellingscontrole voortaan een fulltimebaan is.

## Wat ging er mis?

QuietWriter gebruikt Hunspell-woordenboeken via de pure-Python bibliotheek `spylls`.

Bij sommige lange onbekende woorden kan de suggestie-engine enorm veel mogelijke varianten proberen. Vooral het Nederlandse OpenTaal-woordenboek bevat MAP-regels en samenstellingsregels waarmee het aantal kandidaten heel snel kan groeien.

Het gevolg was niet dat QuietWriter netjes crashte.

Nee.

Het bleef gewoon heel toegewijd suggesties zoeken.

En zoeken.

En zoeken.

Dat is bewonderenswaardig voor een woordenboek, maar minder handig voor een schrijfprogramma.

## Wat is opgelost?

QuietWriter geeft de dure suggestiefase nu een tijdsbudget.

Na ongeveer één seconde stopt het genereren van nieuwe edit-kandidaten en mag de snellere suggestiefase het overnemen.

Daardoor blijven ook lastige woorden zoals lange fantasienamen, rare samenstellingen en testmonsters van tientallen letters de interface niet meer minutenlang gijzelen.

Normale correcties blijven gewoon werken.

## Ook nieuw: kies je woordenboek

Bij **Instellingen → Spelling** kun je nu niet alleen de taal kiezen, maar ook welke gevonden woordenboekbron QuietWriter gebruikt.

Afhankelijk van wat op je computer aanwezig is kun je kiezen uit:

- Meegeleverd
- ONLYOFFICE
- LibreOffice
- OpenOffice
- zelf toegevoegd Hunspell-woordenboek

De keuze wordt lokaal onthouden. Verdwijnt een bron later, dan valt QuietWriter veilig terug op een ander gevonden woordenboek voor dezelfde taal.

## Voor wie is deze update?

Voor iedereen met 1.3.0.

Zeker als je:
- Nederlandse spelling gebruikt;
- fantasienamen schrijft;
- graag lange samenstellingen maakt;
- of ooit hebt gedacht: “Aaaaaaaaaaaaaaaaaaaa lijkt me een prima testwoord.”

## Windows

QuietWriter blijft portable.

Pak de ZIP volledig uit en start:

`QuietWriter.exe`

Geen installatie nodig.

---

# English

## QuietWriter 1.3.1 — long made-up words are allowed to be weird again

QuietWriter 1.3.1 is a small hotfix with one very specific skill:

**If you like long words that do not exist, QuietWriter no longer gets stuck on them.**

Some long unknown words could make the spelling suggestion engine explore an enormous number of alternatives. With the Dutch OpenTaal dictionary, MAP substitutions and compound checks could make that search grow dramatically.

QuietWriter did not really crash.

It just became extremely committed to finding a suggestion.

For minutes.

That is admirable behaviour for a dictionary and less useful behaviour for a writing application.

## The fix

The expensive spelling-suggestion phase now has a time budget.

After roughly one second, QuietWriter stops generating more expensive edit candidates and lets the faster suggestion stage continue.

Normal spelling corrections still work, while pathological words no longer hold the interface hostage.

## Also new: choose your dictionary

In **Settings → Spelling** you can now choose not only the language, but also which discovered dictionary source QuietWriter should use.

Depending on what is available on your computer, that can include:

- Bundled
- ONLYOFFICE
- LibreOffice
- OpenOffice
- a Hunspell dictionary you added yourself

The choice is stored locally. If that source later disappears, QuietWriter safely falls back to another discovered dictionary for the same language.

## Who should install this?

Everyone using 1.3.0.

Especially if you:
- use Dutch spell checking;
- write fantasy names;
- enjoy long compound words;
- or have ever thought: “Aaaaaaaaaaaaaaaaaaaa looks like a perfectly reasonable test word.”

## Windows

QuietWriter remains portable.

Extract the ZIP completely and run:

`QuietWriter.exe`

No installation required.
