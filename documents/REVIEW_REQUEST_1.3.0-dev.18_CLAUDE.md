# Reviewverzoek QuietWriter 1.3.0-dev.18

Wijzig **geen code**. Review en test de build als onafhankelijke reviewer.

## Context

Publieke release blijft 1.2.32. Actieve ontwikkellijn is 1.3.0-dev.18.

Dev.18 start **Planning dichter bij het schrijven**. Bij een leeg hoofdstuk worden opgeslagen, aan dat hoofdstuk gekoppelde scènes uit Planning als zachte hulptekst in de editor geschilderd. Dit moet strikt presentation-only zijn.

Lees eerst:
- `documents/PLANNING_GHOST_PARAGRAPHS_DESIGN.md`
- `documents/RELEASE_NOTES_1.3.0-dev.18.md`
- relevante architectuurregels in `documents/V2_FOUNDATION_RESEARCH.md` en `documents/PRODUCT_AND_UI_PHILOSOPHY.md`

## A. Volledige regressie

1. Draai de volledige pytest-suite met PySide6.
2. Draai `python main.py --smoke-test`.
3. Controleer locales.
4. Draai undefined-names en pyflakes en vergelijk meldingen met dev.17 waar mogelijk.
5. Meld ook de pytest-exitcode na de bekende Linux/Qt-teardown.

## B. Harde presentation-only grens

Maak een boek met een leeg hoofdstuk en gekoppelde Planning-scènes met herkenbare markers in titel, synopsis, locatie, personages, doel, conflict, uitkomst en notities.

Controleer dat zichtbare ghostinformatie:
- nooit in `editor.source_text()` of `QTextDocument.toPlainText()` staat;
- het hoofdstukbestand op schijf byte-inhoudelijk niet wijzigt door alleen tonen/verbergen/repaint/scroll/resize;
- niet meetelt in hoofdstuk- of boektelling;
- niet via Zoeken wordt gevonden;
- niet door spelling als manuscripttekst wordt gezien;
- niet in export/manuscript-AI-context terechtkomt;
- geen dirty-status, autosave of Undo-command veroorzaakt.

Let expliciet op dat Planning-notities en status **niet** in de ghostlaag worden getoond; het paneel `In dit hoofdstuk` mag ze wel blijven tonen.

## C. Leeg/niet-leeg gedrag

Test minimaal:
1. leeg hoofdstuk + gekoppelde scène -> hulp zichtbaar;
2. eerste echte letter -> hulp direct weg;
3. Undo of volledig leegmaken -> hulp terug;
4. alleen een spatie/newline -> beoordeel en rapporteer het gedrag; fase 1 definieert Qt-document-leeg als leeg;
5. hoofdstuk wisselen tussen wel/geen gekoppelde scènes;
6. meerdere scènes in opgeslagen volgorde;
7. zoveel scènes dat ze niet allemaal in het zichtbare vlak passen -> rustige `… en N meer` degradatie;
8. geschiedenispreview/corrupt alleen-lezenhoofdstuk -> geen ghostlaag.

## D. Planning wijzigen

Open een leeg hoofdstuk met ghostlaag, ga naar Planning, wijzig titel/synopsis/personages/doel/conflict/uitkomst en ga terug naar Schrijven. Controleer dat de ghostlaag direct de opgeslagen nieuwe gegevens toont zonder herstart of heropenen van het boek.

Test ook corrupte en toekomstige Planning-data: de normale editor moet bruikbaar blijven en er mag geen stale oude ghostinformatie blijven hangen.

## E. Instelling

Controleer `Instellingen > Uiterlijk > Planninghulp in editor`:
- default = Tonen;
- Verbergen haalt de laag na Opslaan direct weg;
- Tonen brengt hem bij een leeg hoofdstuk terug;
- de instelling verandert geen manuscript- of Planning-data;
- vormgeving past bij de in dev.16/17 geharmoniseerde Instellingen-pagina.

## F. Visueel/performance

Profileer of inspecteer specifiek:
- paintkosten bij een lang, niet-leeg hoofdstuk met gekoppelde scènes: de feature mag geen volledige brontekst per repaint scannen;
- resize/scroll/DPI indien mogelijk;
- licht en donker thema;
- overlap met cursor, image cards, scènebreukpainting en editor margins.

## G. Versie-audit

Zoek naar **actuele** statusverwijzingen die nog ten onrechte 1.3.0-dev.17 of een oudere actieve ontwikkelversie noemen. Historische changelog/release-notes moeten juist historisch blijven en niet worden herschreven. README.md en README_EN.md zijn bewust niet gewijzigd.

## Rapportage

Classificeer als:
- blocker vóór dev.19;
- wel oplossen vóór 1.3.0;
- backlog/polish;
- niet getest.

Geef bij bevindingen een concrete reproductie en de kleinste veilige oplossingsrichting. Wijzig geen code.
