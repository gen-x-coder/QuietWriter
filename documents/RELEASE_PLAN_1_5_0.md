# QuietWriter 1.5.0 — releaseprocedure

Status: nog niet vrijgegeven; eerst volledige Qt/Windows- en AI-regressietests.

1. Controleer de broncode en testuitslagen van de kandidaat; test de EXE inclusief smoke-test lokaal of in Windows CI.
2. Push dezelfde gecontroleerde commit/snapshot naar GitHub repository `quietwriter-dev`.
3. Push dezelfde goedgekeurde broncode naar de publieke GitHub repository `quietwriter`.
4. Start **uitsluitend via de publieke repository** de Windows-buildworkflow. De dev-repository heeft geen beschikbare GitHub Actions-minuten.
5. Verifieer het Windows-buildartifact en de EXE (opstarten, smoke-test, geheugen en AI-instellingen).
6. Maak op `quietwriter` een nieuwe **pre-release** met de gecontroleerde EXE en release notes (geen stable release).

Geen upload, push, workflow-start of pre-release vóór expliciete release-go op de geteste kandidaat.
De experimentele updater blijft afgeschermd achter het speciale lege `.quietwriter-update-pilot`-bestand.
