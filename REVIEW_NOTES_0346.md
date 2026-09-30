# Review QuietWriter 0.34.6

Deze release is een kleine afronding van reviewronde 41.

## Verplicht

1. Koude start zonder boek: open het venster en controleer via runtime dat `planning_context_button.isEnabled()` **False** is.
2. Open een boek via de Boekenplank: knop wordt **True** en de Planning-contextdialoog opent nog steeds normaal.
3. Herhaal hoofdstukwissel, AI-paneel dicht/open, Nieuw gesprek, Planning → Inhoud en boek opnieuw openen. De knop blijft correct.
4. Simuleer kapotte v1 en nieuwere v2 Planning met een actieve Planning-selectie. De AI-vraag moet doorgaan zonder Planning en het bericht/contextstuk moet `Planning niet beschikbaar — <reden>` bevatten.
5. Nep-provider: bevestig opnieuw dat hoofdstukplanning-preview nog steeds niet automatisch in de systeemprompt verschijnt.
6. Draai `pytest` en `pytest tests/legacy`; alleen de twee bekende fonttests mogen falen.

Geen nieuwe UI-layout of schemawijzigingen in deze build.
