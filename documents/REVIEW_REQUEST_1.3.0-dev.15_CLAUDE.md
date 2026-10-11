# Reviewopdracht QuietWriter 1.3.0-dev.15

Wijzig geen code. Review deze snapshot als onafhankelijke tester.

1. Draai de volledige PySide6-testsuite, smoke-test, locale-check, undefined-names en pyflakes.
2. Controleer Boekdetails in minimaal een licht en donker thema: QDateEdit moet visueel aansluiten op QLineEdit/QComboBox/QSpinBox.
3. Controleer Boekomslag zonder eigen omslag: duidelijke 1:1,6 placeholder, tekst Geen omslag, knop Omslag verwijderen disabled.
4. Kies een geldige omslag: preview zichtbaar en Omslag verwijderen enabled. Verwijder hem: placeholder terug en remove disabled; pas Opslaan maakt dit definitief.
5. Controleer regressie van Woorddoel, einddatum, Vandaag geschreven en versieherstel.
6. Doe een versie-audit: publieke stabiele release is 1.2.32 en actuele ontwikkelsnapshot is 1.3.0-dev.15. Historische documenten mogen historische versies behouden.
7. README.md en README_EN.md mogen niet gewijzigd zijn.

Rapporteer blockers, regressies, visuele inconsistenties en concrete aanbevelingen; wijzig niets.
