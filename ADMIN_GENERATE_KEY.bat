@echo off
title SKD TOOL - Admin License Key Generator Dashboard
cd /d "%~dp0"
python admin_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Running CLI Generator fallback...
    python key_generator.py
    pause
)
