# QuietWriter dev.41 — focusmodus (reviewkandidaat)

## Functionaliteit

De editor heeft een knop **Focusmodus** naast de tekstbreedtekeuze en de sneltoets `Ctrl+Shift+F`.
De modus verbergt tijdelijk de inhoudsboom, het rechter gereedschapspaneel en het uitklaptabje.
Bij afsluiten worden precies de zijpanelen hersteld die ervoor zichtbaar waren; de opgeslagen
paneelbreedtes en tekstbreedte blijven behouden. De editor krijgt na de omschakeling focus.
Een gereedschap openen of de inhoudsboom bedienen sluit eerst de focusmodus af.
De teksten zijn toegevoegd in alle vijf talen.

## Testen op Windows (visueel)

1. Open een manuscript met zowel Inhoud als de Meelezer zichtbaar. Schakel Focusmodus in.
   De editor vult de vrijgekomen ruimte. Druk Ctrl+Shift+F: beide panelen komen terug.
2. Verberg eerst zelf Inhoud, zet Focusmodus aan en weer uit: Inhoud moet verborgen blijven.
3. Wijzig Tekstbreedte terwijl Focusmodus aanstaat en keer terug: de breedte blijft staan.
4. Open vanuit Focusmodus een rechter gereedschap: de focusmodus sluit en het gereedschap opent.
5. Controleer in een smal venster of de extra knop goed past; controleer de vijf talen.
6. Schrijf, bewaar en heropen een hoofdstuk: de nieuwe UI-status mag manuscriptinhoud niet wijzigen.

## Bekende beperkingen

- De exacte Qt-schermindeling is hier niet op Windows getest.
- De volledige regressies zijn niet uitgevoerd; de gerichte bron- en taaltests zijn wel gedraaid.
- De OpenRouter-foutafhandeling en de bredere Meelezer-weergave zijn gepland voor de Meelezer-iteratie;
  de fout `Provider returned error` moet in gewone taal en met handelingsadvies worden getoond.
- De interne versiemetadata staan nog op 1.5.0-dev.28; het label dev.41 verwijst naar de bronreview.
- De updater is niet geactiveerd; de publieke GitHub-release en de bestaande handmatige updater zijn ongewijzigd.
