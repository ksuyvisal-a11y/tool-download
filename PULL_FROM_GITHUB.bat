@echo off
title SKD TOOL - Pull from GitHub
cd /d "%~dp0"
echo ========================================
echo     PULLING LATEST CODE FROM GITHUB...
echo ========================================
echo.

set "GIT_CMD=git"
where git >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Git\cmd\git.exe" (
        set "GIT_CMD=C:\Users\%USERNAME%\AppData\Local\Programs\Git\cmd\git.exe"
    )
)

"%GIT_CMD%" pull origin main

echo.
echo ========================================
echo       UPDATE COMPLETE!
echo ========================================
pause
