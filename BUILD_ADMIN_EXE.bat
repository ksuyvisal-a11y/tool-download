@echo off
setlocal enabledelayedexpansion
title [SKD ADMIN] Compiling Standalone Admin Key Generator (.exe)...
cd /d "%~dp0"

echo =========================================================================
echo    [SKD ADMIN] COMPILING STANDALONE ADMIN KEY GENERATOR (.EXE)
echo =========================================================================
echo.

echo [1/3] Checking and generating app icon...
python build_icon.py

echo.
echo [2/3] Building Standalone ADMIN_KEY_GENERATOR.exe with PyInstaller...
python -m PyInstaller --clean --noconfirm admin_generator.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Admin build failed! Check logs above.
    pause
    exit /b 1
)

echo.
echo [3/3] Verification...
if exist "dist\ADMIN_KEY_GENERATOR.exe" (
    echo.
    echo =========================================================================
    echo  SUCCESS! Standalone Admin Key Generator created!
    echo  Location: "%~dp0dist\ADMIN_KEY_GENERATOR.exe"
    echo =========================================================================
    echo.
)

pause
