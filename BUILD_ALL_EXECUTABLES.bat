@echo off
setlocal enabledelayedexpansion
title [SKD STUDIO] Compiling All Standalone Apps (.exe)...
cd /d "%~dp0"

echo =========================================================================
echo       ⚡ SKD STUDIO - COMPILING ALL STANDALONE EXECUTABLES (.EXE)
echo =========================================================================
echo.

echo [1/3] Generating Icons...
python build_icon.py

echo.
echo [2/3] Compiling Main SKD_TOOL.exe...
python -m PyInstaller --clean --noconfirm skd_tool.spec

echo.
echo [3/3] Compiling Admin Key Generator ADMIN_KEY_GENERATOR.exe...
python -m PyInstaller --clean --noconfirm admin_generator.spec

echo.
echo =========================================================================
echo                           BUILD REPORT
echo =========================================================================
if exist "dist\SKD_TOOL.exe" (
    echo [✓] Main App:       "%~dp0dist\SKD_TOOL.exe"
)
if exist "dist\ADMIN_KEY_GENERATOR.exe" (
    echo [✓] Admin App:      "%~dp0dist\ADMIN_KEY_GENERATOR.exe"
)
echo =========================================================================
echo.
pause
