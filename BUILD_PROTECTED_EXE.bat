@echo off
title SKD CYBERGUARD - ENTERPRISE ARMOR COMPILATION
cls
echo =====================================================================
echo   SKD TOOL - ENTERPRISE ANTI-DECOMPILATION & CODE ARMOR BUILDER
echo =====================================================================
echo.

echo [1/3] Encrypting and Armor-Shielding all Python source modules...
python code_armor.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Code Armor encryption failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Terminating existing processes and cleaning build cache...
powershell -Command "Stop-Process -Name SKD_TOOL -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 500; Remove-Item -Force 'dist\SKD_TOOL.exe' -ErrorAction SilentlyContinue"

echo.
echo [3/3] Compiling Armored Binary Executable with PyInstaller...
python -m PyInstaller --clean --noconfirm skd_tool.spec

echo.
if exist "dist\SKD_TOOL.exe" (
    echo =====================================================================
    echo   [SUCCESS] ARMORED EXECUTABLE GENERATED: dist\SKD_TOOL.exe
    echo   [SHIELD] 100%% Encrypted In-Memory Bytecode Containers.
    echo   [SHIELD] Anti-Decompiler & Anti-Pyinstxtractor Protection Active!
    echo =====================================================================
) else (
    echo [ERROR] Build failed! Check the logs above.
)
pause
