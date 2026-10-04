# QuietWriter 1.0.0-rc4

RC4 is een kleine dataveiligheids- en UI-tekstrelease bovenop de functioneel bevroren RC3.

## Wijzigingen

- De Schrijverspersona kan nu veilig omgaan met een `schrijver.md` dat tijdens een open sessie door syncsoftware is verwijderd.
- Een corrupte persona wordt niet overschreven. Lokale wijzigingen worden eerst als herstelkopie onder `archive/persona/` bewaard, waarna afsluiten veilig kan doorgaan.
- Nederlandse en Engelse meldingen gebruiken weer echte witregels in plaats van zichtbare `\n`.
- Het persoonlijke woordenboek en de permanente negeerlijst lezen voor iedere write opnieuw de schijfversie in, nemen de unie en schrijven atomair terug.
- De write-audit en overdrachtsdocumentatie zijn aangepast aan deze laatste gevonden routes.

## Scope

Geen nieuwe v2-functionaliteit. Het Darlings-document blijft ontwerpwerk. Implementatie begint pas na stabiele 1.0.0.

## Validatie vóór stable

RC4 moet nog door de volledige Python 3.12/PySide6-testset, Qt-run, cold start, smoke-test en de relevante Windows-praktijkscenario's.
