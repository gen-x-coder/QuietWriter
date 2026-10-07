# QuietWriter 1.2.5

Deze onderhoudsrelease hardt de nieuwe Open-puntenfunctie uit 1.2.4 af na praktijk- en Qt-review.

## Open punten

- Technische markers zijn compact en bevatten alleen een id.
- Notities worden per boek bewaard in `planning/open_points.json`.
- Knippen/plakken, drag-and-drop en het systeemplakbord kunnen de markers niet meer stil beschadigen of naar andere toepassingen lekken.
- De cursor springt over verborgen markers.
- EPUB, DOCX, PDF en Markdown krijgen defensief ook uit voor-/achterwerk geen markercommentaar mee.

## Responsiviteit en talen

- De rechter gereedschapsrail kan scrollen op lage/HiDPI-schermen.
- Langere hulpteksten in Instellingen krijgen voldoende hoogte.
- Nederlandse fallback blijft Nederlands; Duits, Frans en Spaans vallen bij ontbrekende sleutels terug op Engels.

Duits, Frans en Spaans en het Lamplicht-thema blijven onderdeel van de 1.2-reeks.
