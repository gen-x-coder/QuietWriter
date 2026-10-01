@echo off
rem Maakt een SCHONE portable Windows-release van QuietWriter.
rem De ontwikkelmap mag tests, PPM, reviewnotities en andere rommel bevatten:
rem alleen een expliciete allowlist wordt naar release\stage gekopieerd.
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

python -c "import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)" || (echo Python 3.12 of nieuwer is nodig. & exit /b 1)

rem 1. Schone build-bron maken. Vanaf hier bouwen we NIET meer uit de ontwikkelmap.
python tools\prepare_release.py || exit /b 1
cd /d "%~dp0release\stage"

rem 2. Build-afhankelijkheden/resources uitsluitend in de stage voorbereiden.
python -m pip install --upgrade PySide6 spylls requests pyinstaller || exit /b 1
python tools\fetch_bundled_fonts.py || exit /b 1
python tools\fetch_dictionaries.py || exit /b 1
python packaging\make_version_info.py || exit /b 1

rem 3. Portable onedir bouwen.
pyinstaller --noconfirm --clean packaging\quietwriter.spec || exit /b 1

for /f "tokens=2 delims==" %%v in ('findstr /r /c:"__version__" quietwriter\__init__.py') do set VER=%%~v
set VER=!VER: =!
set VER=!VER:"=!

rem 4. Alleen het PyInstaller-resultaat naar de publieke release-output kopieren.
set OUT=%~dp0release\QuietWriter-!VER!
if exist "!OUT!" rmdir /s /q "!OUT!"
mkdir "!OUT!" || exit /b 1
xcopy /e /i /q /y "dist\QuietWriter\*" "!OUT!\" >nul || exit /b 1

rem 5. Release hygiene: bron/tests/PPM mogen absoluut niet in de distributiemap staan.
if exist "!OUT!\ppm" (echo FOUT: ppm staat in de release. & exit /b 1)
if exist "!OUT!\tests" (echo FOUT: tests staan in de release. & exit /b 1)
if exist "!OUT!\.git" (echo FOUT: .git staat in de release. & exit /b 1)
for /r "!OUT!" %%f in (REVIEW_NOTES_* QUIETWRITER_REVIEW_FINDINGS_* TUSSENTIJDS_RAPPORT_*) do if exist "%%f" (echo FOUT: ontwikkelrapport in release: %%f & exit /b 1)

rem 6. Distributie-zip + hash maken naast de schone releasemap.
cd /d "%~dp0"
set ZIP=release\QuietWriter-!VER!-windows-portable.zip
if exist "!ZIP!" del /q "!ZIP!"
powershell -NoProfile -Command "Compress-Archive -Force -Path 'release\QuietWriter-!VER!' -DestinationPath '!ZIP!'; $h=(Get-FileHash '!ZIP!' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter-!VER!-windows-portable.zip') | Out-File -Encoding ascii '!ZIP!.sha256'" || exit /b 1

echo.
echo Klaar.
echo EXE: release\QuietWriter-!VER!\QuietWriter.exe
echo ZIP: !ZIP!
echo De ontwikkelmap is niet gebruikt als distributiemap.
endlocal
