# QuietWriter 1.2.32 — migratiedialoog en releasepolish

QuietWriter 1.2.32 is een kleine polishrelease bovenop de afgeronde manuscriptarchitectuur van 1.2.31.

De eenmalige manuscriptsyntaxmigratie gebruikt nu volledig door QuietWriter beheerde, vertaalde knoppen. In een Nederlandse omgeving zie je **Boek bijwerken** en **Niet openen** in plaats van de Engelstalige Qt-knoppen Yes en Cancel. **Boek bijwerken** maakt eerst het bestaande herstelpunt, voert daarna de veilige migratie uit en opent vervolgens het boek. **Niet openen** verandert niets aan het boek en opent het niet.

Ook de extra dialoog voor dubbelzinnige legacy-backslashes gebruikt dezelfde expliciete, vertaalde afsluitactie. Aan de manuscriptsyntaxis, opslag, migratiedetectie en DocumentView-architectuur zelf is ten opzichte van 1.2.31 niets gewijzigd.

Deze versie is bedoeld als bronbasis voor de volgende Windows releasecandidate-build.
