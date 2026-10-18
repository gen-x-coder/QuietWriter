@echo off
rem Maakt een SCHONE, bevriesbare portable Windows-release van QuietWriter.
rem De ontwikkelmap mag tests, reviewnotities en andere rommel bevatten:
rem alleen een expliciete allowlist wordt naar release\stage gekopieerd.
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem 0. Windows-builds gebruiken bewust de vaste Python/pip-basis waarop QuietWriter is getest.
python -c "import sys; sys.exit(0 if sys.version_info[:3] == (3,12,10) else 1)" || (
    echo FOUT: deze QuietWriter-build vereist exact Python 3.12.10.
    python --version
    exit /b 1
)
python -c "import pip,sys; sys.exit(0 if pip.__version__ == '26.2.1' else 1)" || (
    echo FOUT: deze QuietWriter-build vereist exact pip 26.2.1.
    python -m pip --version
    exit /b 1
)

set "SOURCE_COMMIT=unknown"
for /f "delims=" %%c in ('git rev-parse HEAD 2^>nul') do set "SOURCE_COMMIT=%%c"
echo Broncommit: !SOURCE_COMMIT!

python -c "import pyflakes" >nul 2>&1 || python -m pip install pyflakes || exit /b 1
python tools\check_undefined_names.py || exit /b 1

rem Oude stagingmap eerst Windows-native verwijderen; dit is robuuster in OneDrive/syncmappen.
set "STAGE=%~dp0release\stage"
if exist "%STAGE%" (
    echo Oude stagingmap verwijderen...
    rmdir /s /q "%STAGE%"
    if exist "%STAGE%" (
        echo FOUT: release\stage kon niet volledig worden verwijderd.
        echo Sluit QuietWriter/Explorer-vensters die deze map gebruiken en probeer opnieuw.
        exit /b 1
    )
)

rem 1. Schone build-bron maken. Vanaf hier bouwen we NIET meer uit de ontwikkelmap.
python tools\prepare_release.py || exit /b 1
cd /d "%~dp0release\stage"

rem 2. Runtime-afhankelijkheden exact vastzetten. --no-deps voorkomt stille versieverschuivingen.
python -m pip install --disable-pip-version-check --no-deps -r packaging\requirements-runtime.lock || exit /b 1

rem 2b. MSVC beschikbaar maken. Een gewone PowerShell/cmd is voldoende als VS Build Tools/Community is geinstalleerd.
where cl >nul 2>&1
if errorlevel 1 (
    set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
    if not exist "!VSWHERE!" (
        echo FOUT: vswhere/cl niet gevonden. Installeer Visual Studio Build Tools met Desktop development with C++.
        exit /b 1
    )
    set "VSINSTALL="
    for /f "usebackq delims=" %%i in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSINSTALL=%%i"
    if not defined VSINSTALL (
        echo FOUT: Visual C++ build tools zijn niet gevonden.
        exit /b 1
    )
    call "!VSINSTALL!\Common7\Tools\VsDevCmd.bat" -arch=x64 -host_arch=x64 >nul || exit /b 1
)
where cl >nul 2>&1 || (echo FOUT: cl.exe is na MSVC-initialisatie nog steeds niet beschikbaar. & exit /b 1)

rem 2c. PyInstaller + builddependencies exact pinnen; bootloader wordt uit bron gecompileerd.
set PYINSTALLER_COMPILE_BOOTLOADER=1
python -m pip install --disable-pip-version-check --force-reinstall --no-deps --no-binary pyinstaller -r packaging\requirements-build.lock || exit /b 1

python tools\fetch_bundled_fonts.py || exit /b 1
python packaging\make_version_info.py || exit /b 1
python tools\render_release_readme.py --template documents\LEESMIJ.txt --version-file quietwriter\__init__.py --out documents\LEESMIJ.txt || exit /b 1

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

copy /y "documents\LEESMIJ.txt" "!OUT!\LEESMIJ.txt" >nul || exit /b 1
if not exist "!OUT!\LEESMIJ.txt" (echo FOUT: LEESMIJ.txt ontbreekt naast QuietWriter.exe. & exit /b 1)

rem SHA-256 van de losse exe bewaren voor VirusTotal/false-positive meldingen.
powershell -NoProfile -Command "$h=(Get-FileHash '!OUT!\QuietWriter.exe' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter.exe') | Out-File -Encoding ascii '%~dp0release\QuietWriter-!VER!-exe.sha256'; Write-Host ('EXE SHA-256: ' + $h)" || exit /b 1

rem 5. Release hygiene: bron/tests/reviewmateriaal mogen absoluut niet in de distributiemap staan.
if exist "!OUT!\ppm" (echo FOUT: ppm staat in de release. & exit /b 1)
if exist "!OUT!\tests" (echo FOUT: tests staan in de release. & exit /b 1)
if exist "!OUT!\.git" (echo FOUT: .git staat in de release. & exit /b 1)
if exist "!OUT!\QuietWriter DEV.cmd" (echo FOUT: interne DEV-launcher staat in de release. & exit /b 1)
if exist "!OUT!\QuietWriter PROD.cmd" (echo FOUT: interne PROD-launcher staat in de release. & exit /b 1)
for /r "!OUT!" %%f in (REVIEW_NOTES_* QUIETWRITER_REVIEW_FINDINGS_* TUSSENTIJDS_RAPPORT_*) do if exist "%%f" (echo FOUT: ontwikkelrapport in release: %%f & exit /b 1)

rem 6. Velopack: portable zip + updatefeed maken.
rem    vpk is een .NET-tool: eenmalig "dotnet tool install -g vpk" (versie gelijk aan velopack in requirements).
rem    Velopack vervangt bij een update alleen de programmamap; boeken, instellingen en logs staan daarbuiten.
cd /d "%~dp0"
where vpk >nul 2>&1 || (echo FOUT: vpk ontbreekt. Installeer met: dotnet tool install -g vpk & exit /b 1)
for /f "tokens=2 delims==" %%v in ('findstr /b /c:"velopack==" packaging\requirements-runtime.lock') do set VELOPACK_VER=%%v
for /f "tokens=2" %%v in ('dotnet tool list -g ^| findstr /i /b /c:"vpk "') do set VPK_VER=%%v
echo velopack (Python): !VELOPACK_VER!   vpk: !VPK_VER!
if not "!VPK_VER!"=="!VELOPACK_VER!" (
    echo FOUT: vpk !VPK_VER! hoort gelijk te zijn aan velopack !VELOPACK_VER! uit packaging\requirements-runtime.lock.
    echo Los op met: dotnet tool update -g vpk --version !VELOPACK_VER!
    exit /b 1
)
set VPK_OUT=release\velopack
if exist "!VPK_OUT!" rmdir /s /q "!VPK_OUT!"
vpk pack --packId LucasBonsel.QuietWriter --packVersion !VER! --packDir "release\QuietWriter-!VER!" --mainExe QuietWriter.exe --packTitle QuietWriter --packAuthors "Lucas Bonsel" --icon quietwriter\resources\quietwriter.ico --outputDir "!VPK_OUT!" || exit /b 1

set PORTABLE=
for %%f in ("!VPK_OUT!\*Portable.zip") do set "PORTABLE=%%f"
if not defined PORTABLE (echo FOUT: Velopack heeft geen Portable.zip gemaakt. & exit /b 1)
if not exist "!VPK_OUT!\releases.win.json" (echo FOUT: updatefeed releases.win.json ontbreekt. & exit /b 1)
rem Testfeed: dezelfde inhoud onder de naam die alleen testkopieen lezen
rem (.quietwriter-update-pilot). Zie documents\RELEASE_PROCESS.md, drie standen.
copy /y "!VPK_OUT!\releases.win.json" "!VPK_OUT!\releases.pilot.json" >nul || exit /b 1
if not exist "!VPK_OUT!\releases.pilot.json" (echo FOUT: testfeed releases.pilot.json ontbreekt. & exit /b 1)
python -c "import sys,zipfile; n={i.replace(chr(92),chr(47)).lower() for i in zipfile.ZipFile(sys.argv[1]).namelist()}; need=['update.exe','current/quietwriter.exe']; miss=[x for x in need if x not in n]; print('Portable.zip-inhoud OK' if not miss else 'FOUT: ontbreekt in Portable.zip: '+', '.join(miss)); sys.exit(1 if miss else 0)" "!PORTABLE!" || exit /b 1

rem 7. Vaste assetnaam voor de downloadlink op dutchscrum.nl en GitHub (/releases/latest/download/...).
set ZIP=release\QuietWriter-windows-portable.zip
copy /y "!PORTABLE!" "!ZIP!" >nul || exit /b 1
powershell -NoProfile -Command "$h=(Get-FileHash '!ZIP!' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter-windows-portable.zip') | Out-File -Encoding ascii 'release\QuietWriter-windows-portable.zip.sha256'" || exit /b 1

rem 8. Bewijsbestand met exacte buildomgeving + beide hashes.
python "release\stage\tools\write_build_manifest.py" --version "!VER!" --source-commit "!SOURCE_COMMIT!" --exe "release\QuietWriter-!VER!\QuietWriter.exe" --zip "!ZIP!" --output "release\QuietWriter-!VER!-build-manifest.txt" || exit /b 1

echo.
echo Klaar.
echo EXE: release\QuietWriter-!VER!\QuietWriter.exe
echo PORTABLE ZIP: !ZIP!
echo MANIFEST: release\QuietWriter-!VER!-build-manifest.txt
echo.
echo Publiceren op GitHub-release v!VER! in drie standen (zie documents\RELEASE_PROCESS.md):
echo   1. Test (pre-release):   !ZIP!, !VPK_OUT!\*-full.nupkg en !VPK_OUT!\releases.pilot.json
echo   2. Uitgebracht:          pre-release uitvinken (gebruikers: melding + downloadpagina)
echo   3. Bijwerken open:       !VPK_OUT!\releases.win.json erbij uploaden (een klik bijwerken voor iedereen)
echo   Gebruik hier NIET "vpk upload github": die zet releases.win.json meteen online.
echo Deze binaries niet opnieuw bouwen na reputatietesten; publiceer exact dezelfde bytes.
endlocal
