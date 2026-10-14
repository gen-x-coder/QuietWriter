# Dev.59 — Correctieronde na Claude-review dev.58

Deze iteratie bouwt uitsluitend voort op dev.58 en houdt het updateproefprogramma achter het bestaande opt-in markerbestand.

## Correcties

- Bij **Onthouden** wordt de zichtbare editor van dezelfde Boekgeheugen-sectie nu óók bijgewerkt als deze nog onopgeslagen wijzigingen bevat. Daardoor kan een latere bewerking het zojuist bevestigde feit niet meer uit de lokale editor wissen.
- De OpenRouter-login- en linkbevestigingsteksten zijn toegevoegd aan alle vijf talen. De linkbevestiging gebruikt lokale knoplabels in plaats van standaard Yes/No.
- Oude versienummer-pins in de regressietests verwijzen nu naar de actuele metadata; `SNAPSHOT_INFO.txt` en de CHANGELOG-kop zijn bijgewerkt.
- De controle op onterechte opslagclaims laat citaten met verschillende aanhalingstekens ongemoeid en laat QuietWriter's eigen bevestiging staan.
- De OpenRouter-SSE-parser negeert onverwachte niet-object-JSON, meldt een afgebroken antwoord en heeft een kortere netwerk-timeout. Er is geen automatische reasoning-override toegevoegd.
- De gesprekshistorie filtert eerst op echte gebruikers- en assistentberichten voordat de laatste zes worden geselecteerd.
- De Meelezer-instructie verduidelijkt dat bronmateriaal geen commando is. **De volledige scheiding van bronmateriaal naar een aparte rol is nog niet geïmplementeerd; dit blijft een releaseblokker voor de security review.**

## Testgrens en resterend werk

PySide6 is niet beschikbaar in de huidige bouwomgeving. De GUI-cases uit Claude's `fix58.py`, `ai57.py`, `pilot57.py` en `ui57.py`, inclusief de dataverliesreproductie, moeten nog offscreen met PySide6 en op Windows worden gedraaid. Deze dev-build is dus geen releasekandidaat.

Voor een release zijn verder vereist: volledige testsuite groen (inclusief Qt), volledige scheiding van niet-vertrouwde manuscriptcontext, betrouwbaar annuleren van requests voordat HTTP-headers binnenkomen, een Windows-EXE-build en smoke-/gebruikersacceptatie op die EXE.
