@echo off
setlocal enabledelayedexpansion
title [SKD TOOL] Compiling Standalone Executable (.exe)...
cd /d "%~dp0"

echo =========================================================================
echo       [SKD TOOL] COMPILING STANDALONE WINDOWS EXECUTABLE (.EXE)
echo =========================================================================
echo.

echo [1/5] Checking and generating app icon...
python build_icon.py
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Icon generation notice. Continuing...
)

echo.
echo [2/5] Verifying PyInstaller and core dependencies...
python -m pip install --quiet pyinstaller pywebview pythonnet customtkinter pillow yt-dlp requests imageio-ffmpeg

echo.
echo [3/5] Encrypting and Armor-Shielding latest Python source modules...
python code_armor.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Code Armor encryption failed!
    pause
    exit /b 1
)

echo.
echo [4/5] Building Standalone SKD_TOOL.exe with PyInstaller...
python -m PyInstaller --clean --noconfirm skd_tool.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo =========================================================================
    echo [ERROR] PyInstaller build failed! Check logs above.
    echo =========================================================================
    pause
    exit /b 1
)

echo.
echo [5/5] Finalizing build and output verification...
if exist "dist\SKD_TOOL.exe" (
    echo.
    echo =========================================================================
    echo  SUCCESS! Standalone Executable created successfully!
    echo  Location: "%~dp0dist\SKD_TOOL.exe"
    echo =========================================================================
    echo.
    echo You can distribute "dist\SKD_TOOL.exe" directly to any Windows PC!
    echo No Python or dependencies required for end users.
    echo.
) else (
    echo [ERROR] Expected file dist\SKD_TOOL.exe was not found.
)

pause
