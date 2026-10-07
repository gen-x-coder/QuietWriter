@echo off
rem Maakt een SCHONE, bevriesbare portable Windows-release van QuietWriter.
rem De ontwikkelmap mag tests, reviewnotities en andere rommel bevatten:
rem alleen een expliciete allowlist wordt naar release\stage gekopieerd.
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem 0. De 1.2.32-RC gebruikt bewust exact de Windows/Python-basis waarop hij is getest.
python -c "import sys; sys.exit(0 if sys.version_info[:3] == (3,12,10) else 1)" || (
    echo FOUT: deze releasecandidate vereist exact Python 3.12.10.
    python --version
    exit /b 1
)
python -c "import pip,sys; sys.exit(0 if pip.__version__ == '26.2.1' else 1)" || (
    echo FOUT: deze releasecandidate vereist exact pip 26.2.1.
    python -m pip --version
    exit /b 1
)

set "SOURCE_COMMIT=unknown"
for /f "delims=" %%c in ('git rev-parse HEAD 2^>nul') do set "SOURCE_COMMIT=%%c"
echo Broncommit: !SOURCE_COMMIT!

python -c "import pyflakes" >nul 2>&1 || python -m pip install pyflakes || exit /b 1
python tools\check_undefined_names.py || exit /b 1

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

python tools\prepare_release.py || exit /b 1
cd /d "%~dp0release\stage"

python -m pip install --disable-pip-version-check --no-deps -r packaging\requirements-runtime.lock || exit /b 1

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

set PYINSTALLER_COMPILE_BOOTLOADER=1
python -m pip install --disable-pip-version-check --force-reinstall --no-deps --no-binary pyinstaller -r packaging\requirements-build.lock || exit /b 1

python tools\fetch_bundled_fonts.py || exit /b 1
python tools\fetch_dictionaries.py || exit /b 1
python packaging\make_version_info.py || exit /b 1

pyinstaller --noconfirm --clean packaging\quietwriter.spec || exit /b 1

for /f "tokens=2 delims==" %%v in ('findstr /r /c:"__version__" quietwriter\__init__.py') do set VER=%%~v
set VER=!VER: =!
set VER=!VER:"=!

set OUT=%~dp0release\QuietWriter-!VER!
if exist "!OUT!" rmdir /s /q "!OUT!"
mkdir "!OUT!" || exit /b 1
xcopy /e /i /q /y "dist\QuietWriter\*" "!OUT!\" >nul || exit /b 1

copy /y "documents\LEESMIJ.txt" "!OUT!\LEESMIJ.txt" >nul || exit /b 1
if not exist "!OUT!\LEESMIJ.txt" (echo FOUT: LEESMIJ.txt ontbreekt naast QuietWriter.exe. & exit /b 1)

powershell -NoProfile -Command "$h=(Get-FileHash '!OUT!\QuietWriter.exe' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter.exe') | Out-File -Encoding ascii '%~dp0release\QuietWriter-!VER!-exe.sha256'; Write-Host ('EXE SHA-256: ' + $h)" || exit /b 1

if exist "!OUT!\ppm" (echo FOUT: ppm staat in de release. & exit /b 1)
if exist "!OUT!\tests" (echo FOUT: tests staan in de release. & exit /b 1)
if exist "!OUT!\.git" (echo FOUT: .git staat in de release. & exit /b 1)
if exist "!OUT!\QuietWriter DEV.cmd" (echo FOUT: interne DEV-launcher staat in de release. & exit /b 1)
if exist "!OUT!\QuietWriter PROD.cmd" (echo FOUT: interne PROD-launcher staat in de release. & exit /b 1)
for /r "!OUT!" %%f in (REVIEW_NOTES_* QUIETWRITER_REVIEW_FINDINGS_* TUSSENTIJDS_RAPPORT_*) do if exist "%%f" (echo FOUT: ontwikkelrapport in release: %%f & exit /b 1)

cd /d "%~dp0"
set ZIP=release\QuietWriter-!VER!-windows-portable.zip
if exist "!ZIP!" del /q "!ZIP!"
powershell -NoProfile -Command "Compress-Archive -Force -Path 'release\QuietWriter-!VER!' -DestinationPath '!ZIP!'; $h=(Get-FileHash '!ZIP!' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter-!VER!-windows-portable.zip') | Out-File -Encoding ascii '!ZIP!.sha256'" || exit /b 1

copy /y "!ZIP!" "release\QuietWriter-windows-portable.zip" >nul || exit /b 1
powershell -NoProfile -Command "$h=(Get-FileHash 'release\QuietWriter-windows-portable.zip' -Algorithm SHA256).Hash.ToLower(); ($h + '  QuietWriter-windows-portable.zip') | Out-File -Encoding ascii 'release\QuietWriter-windows-portable.zip.sha256'" || exit /b 1

python "release\stage\tools\write_build_manifest.py" --version "!VER!" --source-commit "!SOURCE_COMMIT!" --exe "release\QuietWriter-!VER!\QuietWriter.exe" --zip "!ZIP!" --output "release\QuietWriter-!VER!-build-manifest.txt" || exit /b 1

echo.
echo Klaar.
echo EXE: release\QuietWriter-!VER!\QuietWriter.exe
echo ZIP: !ZIP!
echo MANIFEST: release\QuietWriter-!VER!-build-manifest.txt
echo VASTE ZIP: release\QuietWriter-windows-portable.zip
echo Deze RC-binaries niet opnieuw bouwen na reputatietesten; publiceer exact dezelfde bytes.
endlocal
