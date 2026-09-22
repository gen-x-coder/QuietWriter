@echo off
py tools\fetch_bundled_fonts.py
if errorlevel 1 pause
