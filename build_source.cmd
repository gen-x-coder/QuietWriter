@echo off
setlocal
cd /d "%~dp0"
python tools\build_source_zip.py
exit /b %errorlevel%
