# Tussentijds rapport 0.35.3

0.35.3 sluit de 0.35-releasefundamenten af. De startcrash uit 0.35.2 was een ontbrekende `tr`-import. Naast de directe fix is CI uitgebreid met `pyflakes` zodat undefined names voortaan vóór runtime worden gevonden. Een kleine AST-regressietest bewaakt specifiek dat modules die `tr()` aanroepen de helper ook binden.

De Engelse rondgang uit reviewronde 49 is verwerkt. De altijd zichtbare woordtelling, het editor-contextmenu, AI-gebruikerslabel, spellingstatus, Replace all, conflict-/corruptiemeldingen en boekenplankfouten gebruiken nu vertalingssleutels. Planning-statussen en relaties houden hun bestaande canonieke opslagwaarden en vertalen alleen de UI-weergave. Nieuwe boeken krijgen de gelokaliseerde standaardhoofdstuktitel.

De OFL-sjabloonregels zijn verwijderd uit de vier fontlicenties. De Inhoudsboom reserveert extra ruimte voor de actie-kolom zodat `wijzig`/`edit` niet meer onder het inklaptabje valt. De ongebruikte `MainWindow.build_ai_context` is verwijderd.

Lokale basislijn in de ChatGPT-omgeving: current 210 geslaagd + 17 Qt-skips; legacy 426 geslaagd + 284 subtests + 24 Qt-skips; compileall groen. De echte PySide6-, Engelse runtime- en pyflakes-runs staan expliciet in `REVIEW_NOTES_0353.md` voor Claude.
