# Reviewopdracht QuietWriter 1.3.0-dev.11

Wijzig **geen code**. Review en test deze snapshot onafhankelijk.

## 1. Regressie
- volledige pytest-suite met PySide6;
- `python main.py --smoke-test`;
- locales/check_locales;
- undefined-names/pyflakes zoals bij eerdere reviews.

## 2. Versie-audit
Zoek expliciet naar verouderde **actuele** versieverwijzingen. De publieke stabiele release is **1.2.32** en de huidige ontwikkelsnapshot is **1.3.0-dev.11**. Historische release notes/reviews mogen uiteraard hun eigen oude versies blijven noemen. `README.md` en `README_EN.md` zijn bewust niet aangepast.

## 3. Opt-incontract
Controleer dat `writing_progress_enabled` standaard uit staat en dat nergens dagactiviteit wordt verzameld voordat de gebruiker de checkbox zelf inschakelt. De checkbox in Boekdetails en die in Instellingen moeten dezelfde setting gebruiken.

Test uit → aan → uit → aan:
- bestaande dagvoortgang blijft bewaard;
- tijdens uit wordt niets toegevoegd;
- bij opnieuw aan wordt de uitgeschakelde periode niet retroactief meegeteld.

## 4. Telmodel
Test met afzonderlijke geslaagde saves:
- +100 woorden → vandaag +100;
- daarna 20 woorden schrappen → vandaag blijft +100;
- daarna +30 woorden → vandaag +130;
- eerst schrappen en daarna schrijven versus eerst schrijven en daarna schrappen: positieve schrijfproductie mag niet negatief worden;
- import, versieherstel en externe adoptie mogen niet als lokaal geschreven woorden meetellen.

Controleer daggrens op lokale kalenderdatum en corrupt/onbeschrijfbaar progressbestand: nooit manuscriptverlies of crash.

## 5. Boekdoel/deadline
- opslaan, heropenen en drie-weg metadata-merge;
- `.qwbook` roundtrip;
- versieherstel naar een snapshot van vóór/na een doel: het **huidige** doel en de huidige deadline blijven staan;
- deadline zonder woorddoel is niet actief;
- verstreken deadline geeft neutrale tekst zonder rood/achterstandstaal.

## 6. UI/Boekenkast
- boek zonder doel ziet eruit zoals voorheen;
- boek met doel: dunne balk + `x van y woorden`;
- editor: doeltekst, en alleen bij opt-in + positief dagtotaal `vandaag n`;
- Presentatiemodus mag geen nieuwe privacylekken krijgen;
- kijk naar 1280×700 en DPI 125/150% waar mogelijk.

## 7. Architectuur/privacy
Bevestig dat dagvoortgang buiten de werkmap staat, niet in `library.json`, niet in `.qwbook`, en geen boektitels/paden hoeft te bevatten. Controleer ook of dev/stable door `AppLocalDataLocation` voldoende gescheiden blijven.

Classificeer bevindingen als blocker / vóór volgende dev / backlog, en geef waar mogelijk concrete reproducerende tests.
