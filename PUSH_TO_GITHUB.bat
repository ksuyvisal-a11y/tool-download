@echo off
title SKD TOOL - Push to GitHub
cd /d "%~dp0"
echo ========================================
echo       PUSHING CODE TO GITHUB...
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

"%GIT_CMD%" add .
"%GIT_CMD%" commit -m "Update: %date% %time%"
"%GIT_CMD%" push -u origin main
"%GIT_CMD%" push a11y main
"%GIT_CMD%" push --tags a11y

echo.
echo ========================================
echo       PUSH COMPLETE!
echo ========================================
pause
