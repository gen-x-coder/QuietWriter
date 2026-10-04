# QuietWriter 1.0.0-rc2

RC2 is een stabiliteits- en releasecandidate zonder nieuwe grote functies.

Belangrijk sinds RC1:
- publieke portable package bevat geen interne DEV/PROD launchers;
- Windows smoke gebruikt de echte GUI-process exitcode;
- zoekcache/SQLite-afhandeling is verder afgehard en sluit handles expliciet;
- release-/versiemetadata is bijgewerkt;
- volledige Windows- en Ubuntu-testmatrix was groen in de releasecyclus.

De opgeschoonde rc2-bron is daarnaast op **2 oktober 2026** opnieuw lokaal doorgelicht in reviewronde 56 met Python 3.12.3 / PySide6 6.11.2: 433 actieve tests + 284 subtests groen, 80 Qt-tests groen, startup/smoke groen en 450/451 oude legacytests groen; de enige legacyfailure verwees uitsluitend naar een bewust verwijderd oud document. Zie `VALIDATION.md` voor de volledige context en de daaropvolgende overdraagbaarheidsfixes.

Bekende niet-blokkerende beperking: met OpenRouter free-only kan een bewaard betaald model veilig persisted blijven terwijl de UI na catalogusload een gratis selectie toont. Dit is UX-verwarring, geen dataverlies.

Voor stabiele 1.0 blijven vooral praktijkchecks over: clean Windows, SmartScreen, DPI, echte providers, oude/grote boeken en langer dagelijks gebruik.
