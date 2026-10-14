@echo off
rem NONPRODUCTION LAB only. Build updater onedir outside the OneDrive build cache.
setlocal EnableExtensions
cd /d "%~dp0.."
python -c "import PyInstaller" || (echo ERROR: Install PyInstaller with pip install -r requirements-dev.txt. & exit /b 1)
set "QW_WORK=%TEMP%\qw-updater-lab-work-%RANDOM%-%RANDOM%"
set "QW_SPEC=%QW_WORK%\spec"
rem Separate output directory from the old onefile build so stale EXEs cannot pass.
set "QW_DIST=release\updater-lab-onedir"
python -m PyInstaller --noconfirm --onedir --console --name QuietWriterUpdaterLab --paths "." --distpath "%QW_DIST%" --workpath "%QW_WORK%\build" --specpath "%QW_SPEC%" tools\quietwriter_updater_lab.py
if errorlevel 1 (
    echo ERROR: updater LAB build failed; DO NOT run a previously built EXE.
    exit /b 1
)
if not exist "%QW_DIST%\QuietWriterUpdaterLab\QuietWriterUpdaterLab.exe" (
    echo ERROR: updater LAB EXE missing; build NOT accepted.
    exit /b 1
)
rem Verify the fresh onedir entrypoint, not any old onefile artifact.
"%QW_DIST%\QuietWriterUpdaterLab\QuietWriterUpdaterLab.exe" --help >nul
if errorlevel 1 (echo ERROR: newly built updater cannot start. & exit /b 1)
echo LAB ONEDIR: %QW_DIST%\QuietWriterUpdaterLab\QuietWriterUpdaterLab.exe
echo Never use this executable on an actual QuietWriter installation.
endlocal
