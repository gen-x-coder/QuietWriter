# Tussentijds rapport 0.31.5

## Aanleiding

Reviewronde 23 verklaarde 0.31.4 groen. Het enige bekende architectuurpunt bleef de centrale adopt-commit: een schrijffout tijdens een recovery-snapshot van bijvoorbeeld Boekgeheugen kon optreden nadat editor en Planning al naar het nieuwe boek waren omgebonden.

## Wijziging

De drie-wegs mergevoorbereiding van Boekprofiel, Boekgeheugen en Boekdetails is verplaatst naar `_prepare_active_book_adoption()`.

Elke pagina exposeert nu een `prepare_adoption()`-stap. Die berekent de merge en maakt, indien nodig, de `conflict_local`-snapshot terwijl de volledige bestaande workspace nog intact is. De daaropvolgende `adopt_book(..., prepared=...)`/`adopt_book_preserving_form(..., prepared=...)` commit gebruikt alleen het vooraf berekende plan en schrijft geen recoveryversie meer.

Ook de conflictmeldingen zijn uit de commitvolgorde gehaald: eerst worden alle pagina's omgebonden, daarna `_active_book` gezet en de revision baseline via `track_book()` gecommit, en pas daarna verschijnen de meldingen.

## Tests lokaal

- Nieuwe 0.31.5 bron-/architectuurtests toegevoegd.
- Bestaande bronasserties voor Boekgeheugen, Boekprofiel en Boekdetails aangepast aan het nieuwe prepared-plan contract.
- Volledige suite in deze omgeving: **546 passed, 27 skipped, 280 subtests passed**.
- Alleen de **2 bekende fonttests** falen doordat `resources/fonts/font_manifest.json` in deze distributieomgeving ontbreekt.
- PySide6 is hier niet geïnstalleerd; de echte runtime/failure-injectiontests staan daarom expliciet in `REVIEW_NOTES_0315.md` voor Claude.

## Niet gewijzigd

De veilige conflictkeuzes, merge-semantiek en Exportflow uit 0.31.4 zijn inhoudelijk niet veranderd. De wat ongelukkige melding `Structuuractie niet uitgevoerd` bij pending publicatietekst blijft als latere UI-polish staan.
