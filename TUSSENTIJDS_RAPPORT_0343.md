# Tussentijds rapport 0.34.3

0.34.3 sluit de twee overgebleven routes rond nieuwere/onbetrouwbare Planning. De expliciete AI Planning-context degradeert naar geen Planning-context in plaats van een Qt-slotexceptie. History weigert een volledige restore voordat een snapshot of live bestand wordt gewijzigd wanneer outline/characters een nieuwer Planning-formaat heeft.

Visueel is de ingeklapte railseparator verhoogd van 1 naar 2 px met dezelfde themakleur. QLabel-auto-indent is uitgeschakeld voor contextkoppen en veldlabels. De statusbalk gebruikt correcte enkelvoud/meervoudsvormen.

Lokale tests: `pytest` 171 passed, 11 skipped. Legacy: 424 passed + 280 subtests, 24 skipped; alleen de twee bekende fontresource-tests falen wegens ontbrekende fonts in deze omgeving.
