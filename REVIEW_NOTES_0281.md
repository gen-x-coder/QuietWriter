# QuietWriter 0.28.1 — reviewnotes voor Claude

Zie `TUSSENTIJDS_RAPPORT_0281.md` voor ontwerpkeuzes en de gevraagde runtime/failure-injectiontests. Focus bij deze ronde op correctness en databehoud; visuele polish van de boekenplankmelding valt buiten deze backend-review.

Belangrijkste contract: een operatie die niet met zekerheid veilig kan worden uitgevoerd moet falen zonder de bestaande live bytes te wijzigen. Herstel mag pas succes teruggeven nadat de teruggezette inhoud opnieuw volgens hetzelfde type-/hashcontract is gevalideerd.
