# Changelog

## 0.7.0

- Versiegeschiedenis toegevoegd aan de rechter gereedschapsbalk.
- Dagarchieven uit eerdere versies worden automatisch zichtbaar in de tijdlijn.
- Handmatig een volledige boekversie maken vanuit het geschiedenisvenster.
- Historische versies alleen-lezen bekijken zonder het huidige manuscript te wijzigen.
- Duidelijke bovenbalk tijdens versiepreview met datum/tijd, Herstellen en Afsluiten.
- Herstellen maakt eerst automatisch een extra veiligheidsversie en probeert bij fouten terug te rollen.
- Versies kunnen een ster krijgen en de tijdlijn kan op versies met ster filteren.
- Hoofdstuktitels worden nu meegenomen door het spellingscontrolepaneel.
- Manifest- en hoofdstukopslag robuuster gemaakt voor Dropbox/Windows file locks: unieke tijdelijke bestanden, retries en gecontroleerde fallback.
- Drag-and-drop commit nu transactioneel: de in-memory hoofdstukvolgorde wordt pas gewijzigd nadat book.json succesvol is opgeslagen.
- Qt-fontinitialisatie aangepast om ongeldige point-size overerving op Windows te voorkomen.
- Testset uitgebreid naar 22 regressietests, waaronder geschiedenis, herstel en Dropbox-achtige PermissionError-situaties.
