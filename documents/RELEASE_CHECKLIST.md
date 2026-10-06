# QuietWriter release-checklist

## Na elke Windows-build

1. Bouw alleen vanuit een **x64 Native Tools Command Prompt for VS**. De release-build compileert de PyInstaller-bootloader zelf.
2. Controleer dat `build_exe.cmd` volledig groen eindigt en noteer de getoonde **EXE SHA-256**.
3. Controleer `release/QuietWriter-<versie>-exe.sha256` en de bestaande ZIP/SHA-256.
4. Start de gebouwde `QuietWriter.exe --smoke-test` en controleer exitcode 0.
5. Test op Windows minimaal: starten, boek openen/opslaan, DOCX import/export en `.qwbook` export/import.
6. Upload de losse `QuietWriter.exe` naar VirusTotal.
7. Bij een Microsoft-melding: dien de exe in via Microsoft Security Intelligence → **Software developer** → **Incorrectly detected as malware**. Vermeld dat QuietWriter een legitieme schrijfapp is die met PyInstaller is gebouwd.
8. Houd onedir, `upx=False` en `console=False`; gebruik geen packers, obfuscatie of onefile-build om scanners te omzeilen.
9. Publiceer pas daarna de portable ZIP en SHA-256 in de publieke GitHub-release.

## False positives

Een generieke ML/heuristiek-detectie bewijst op zichzelf niet dat een bestand schoon of kwaadaardig is. Vergelijk daarom altijd de SHA-256 met de lokaal gebouwde release en gebruik de officiële false-positiveprocedure van de betreffende leverancier.

## Toekomst

Code signing blijft de structurele reputatie-oplossing voor Windows.
