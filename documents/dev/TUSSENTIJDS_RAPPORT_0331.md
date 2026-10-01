# Tussentijds rapport QuietWriter 0.33.1

## Doel
Afsluitende visuele en inhoudelijke correcties op 0.33.0.

## Uitgevoerd
- PROGRAMMA uit de QScrollArea gehaald en als vaste ondersectie van de linkerrail geplaatst.
- Declaratieve group separators toegevoegd voor de ingeklapte rail.
- Renderer blijft puur: ook separators worden uitsluitend uit `RailViewModel` + expanded state afgeleid.
- AI-contextteksten opnieuw gelijkgetrokken met `build_system_prompt`: Persona, Boekprofiel en Boekgeheugen gaan standaard mee; Boekprofiel kan voor dit boek bewust afwijken van Persona.
- Externe-providerprivacy expliciet gemaakt.
- Qt-hoogtetest gebruikt nu het echte app-stylesheet; oude SCHRIJVEN-test aangepast aan AI-CONTEXT.

## Lokale tests
Volledige suite: 576 geslaagd + 280 subtests; 33 Qt-runtime-tests overgeslagen in deze omgeving; alleen de twee bekende fontresource-tests falen.
