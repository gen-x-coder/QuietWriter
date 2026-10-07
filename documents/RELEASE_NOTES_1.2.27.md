# QuietWriter 1.2.27 — Manuscriptsyntax geversioneerd

Deze ontwikkelversie legt de basis voor expliciet versiebeheer van QuietWriter-manuscriptsyntax zonder bestaande boeken stil te migreren.

- Nieuwe boeken en nieuwe DOCX-imports krijgen in `book.json` een expliciet `manuscript_syntax`-profiel met versie en featureflags, waaronder de huidige escaping-capability.
- Bestaande boeken zonder profiel blijven bij openen en normaal opslaan ongewijzigd; de marker wordt niet stil toegevoegd.
- Onbekende toekomstige syntaxversies of featureflags worden geweigerd in plaats van genegeerd.
- Integriteit meldt onversioneerde oudere boeken als waarschuwing, niet als corrupt.
- `inline_runs` gebruikt een lineaire sweep over stijlgrenzen in plaats van per teken alle spans opnieuw te scannen; zwaar opgemaakte lange tekst schaalt daardoor beter.
- Dit is infrastructuur: een expliciete, omkeerbare migratie voor oudere boeken volgt apart en wordt niet automatisch uitgevoerd.
