@echo off
chcp 65001 >nul
title SKD TOOL - Studio Edition (Dev Mode)
cd /d "%~dp0"

echo ===============================================================================
echo                SKD TOOL - UNIVERSAL MEDIA DOWNLOADER ^& CONVERTER
echo ===============================================================================
echo [INFO] Starting SKD TOOL Workspace...
echo.

:: 1. Try Windows user Python path (%LOCALAPPDATA%\Python\pythoncore-3.14-64)
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" app.py
    goto :done
)

:: 2. Try default python command in PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python app.py
    goto :done
)

:: 3. Try py launcher
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 app.py
    goto :done
)

:: 4. Try Programs\Python installations
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" app.py
    goto :done
)
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" app.py
    goto :done
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
    goto :done
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" app.py
    goto :done
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" app.py
    goto :done
)

:: 5. Try LocalAppData Python bin
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    "%LOCALAPPDATA%\Python\bin\python.exe" app.py
    goto :done
)

:: 6. Try standard root Python installations
if exist "C:\Python314\python.exe" (
    "C:\Python314\python.exe" app.py
    goto :done
)
if exist "C:\Python313\python.exe" (
    "C:\Python313\python.exe" app.py
    goto :done
)
if exist "C:\Python312\python.exe" (
    "C:\Python312\python.exe" app.py
    goto :done
)
if exist "C:\Python311\python.exe" (
    "C:\Python311\python.exe" app.py
    goto :done
)

echo.
echo [ERROR] Python executable was not found on your system!
echo Please make sure Python 3.10+ is installed and added to PATH.
echo Download from: https://www.python.org/downloads/
echo.

:done
if %ERRORLEVEL% neq 0 (
    echo.
    echo ===============================================================================
    echo [ERROR] SKD TOOL exited with status code: %ERRORLEVEL%
    echo ===============================================================================
)
echo.
pause
