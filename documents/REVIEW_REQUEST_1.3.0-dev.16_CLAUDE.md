# Reviewopdracht QuietWriter 1.3.0-dev.16

Wijzig geen code. Review deze snapshot als onafhankelijke tester.

1. Draai de volledige PySide6-testsuite, smoke-test, locale-check, undefined-names en pyflakes.
2. Bekijk alle Instellingen-categorieën in minimaal Helder en Nacht/Lamplicht. Controleer dat aan/uit-instellingen visueel hetzelfde formulierpatroon volgen als andere keuzevelden en nergens losse systeemcheckboxes overblijven.
3. Test dat alle vervangen boolean controls dezelfde waarden laden, wijzigen, previewen en opslaan als voorheen: geavanceerde opties, begeleid exporteren, Vandaag geschreven, updatecontrole, slimme aanhalingstekens, AI aan/uit, OpenRouter gratisfilter, thinking, snelacties en spellingscontrole.
4. Controleer afhankelijkheden: AI uit schakelt relevante controls uit; providerwissel toont/verbergt gratisfilter; thinking-control volgt modelcapabilities; feature visibility preview werkt; spellingscontrole blijft live toepasbaar.
5. Controleer actieknoppen en samengestelde controls op uitlijning, breedte en thema-consistentie.
6. Regressietest dev.15 Boekdetails: datumveld en omslagplaceholder/remove-state.
7. Doe een versie-audit: publieke stabiele release is 1.2.32 en actuele ontwikkelsnapshot is 1.3.0-dev.16. Historische documenten mogen historische versies behouden.
8. README.md en README_EN.md mogen niet gewijzigd zijn.

Rapporteer blockers, regressies, visuele inconsistenties en aanbevelingen; wijzig niets.
