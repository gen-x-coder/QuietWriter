# Changelog

## 0.11.0

- De boekenplank is responsive gemaakt: het aantal kolommen wordt uit de beschikbare breedte berekend, zodat vrije horizontale ruimte wordt benut voordat een tweede rij ontstaat.
- Boekkaarten zijn licht vergroot, terwijl omslagtiteltekst kleiner is gemaakt voor langere titels.
- De knop **Details** is van de boekenplank verwijderd. Boekdetails horen nu bij een geopend boek.
- **Boekdetails** is geen popup meer maar een volwaardige centrale pagina in QuietWriter.
- **Instellingen** is geen popup meer maar een volwaardige centrale pagina. Thema- en typografiepreview blijven werken; Annuleren herstelt de vorige preview.
- **Schrijverspersona**, **Instellingen** en **Prullenbak** staan als globale functies onderaan de linkernavigatie.
- De losse **Verhalen**-functie is volledig verwijderd uit UI, startup, opslag, indexering, iconen en broncode.
- QuietWriter maakt geen `stories`-map meer aan. Oude Markdownbestanden kunnen via **Importeren…** als normaal QuietWriter-boek worden geopend.
- De oude stories-index (`story_index.py`) en stories-icoon zijn verwijderd.
- De rechter gereedschapsrail verschijnt alleen bij de editor; Boekdetails en Instellingen gebruiken dezelfde centrale paginanavigatie als de rest van de app.
- 53 regressietests slagen.

## 0.10.9

- Alle QuietWriter-SVG-iconen worden via één thema-afhankelijke renderer ingekleurd.
- AI-rich-text wordt bij themawissels opnieuw opgebouwd met de actieve themakleuren.
