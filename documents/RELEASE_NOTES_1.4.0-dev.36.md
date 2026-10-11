# QuietWriter 1.4.0-dev.36 — Een back-up mag niet vergeten wie er schreef

Deze bouwronde richt zich op de problemen uit Claude's dev.35-review.

**Belangrijkste correctie:** een back-up mag nooit stil accepteren dat een geopend boek buiten QuietWriter is gewijzigd. Als Dropbox of OneDrive een nieuwere tekst heeft binnengebracht, moet QuietWriter het schrijfconflict blijven herkennen.

Ook herstel zonder meegeleverde versiegeschiedenis bewaart nu de bestaande versies. Definitief verwijderen ruimt oude versies van het verwijderde boek op. Spelling behandelt `ĳ` en `ij` gelijk, óók wanneer de woordenboekverwerker terugvalt op eenvoudige suggesties. De zoekindex werkt bij opslaan alleen het gewijzigde hoofdstuk bij. Historische kopieën worden niet meer onder hun definitieve naam opgebouwd, en een mislukte dagkopie verhindert de manuscriptopslag niet.

Back-ups blijven uiteraard een extra vangnet, niet de enige plaats waar je manuscript bewaard wordt. Deze iteratie is nog geen releasecandidate: een onafhankelijke Qt- en Windows-controle van de gewijzigde paden blijft nodig.
