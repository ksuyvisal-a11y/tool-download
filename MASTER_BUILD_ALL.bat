@echo off
title SKD TOOL - DUAL-SHIELD ENTERPRISE PROTECTION SUITE
cls
echo =====================================================================
echo          SKD TOOL - DUAL-SHIELD ENTERPRISE PROTECTION SUITE
echo =====================================================================
echo.
echo Please choose your enterprise protection mode:
echo.
echo  [1] OPTION 1: Start Cloud Backend API Server (100%% Unhackable Cloud API)
echo  [2] OPTION 2: Build Native C Machine-Code Executable (Nuitka C/C++ Binary)
echo  [3] Build Code Armor V2 PyInstaller Executable (Encrypted In-Memory Bytecode)
echo  [4] Exit
echo.
set /p opt="Enter your choice (1-4): "

if "%opt%"=="1" (
    cd server
    start RUN_CLOUD_SERVER.bat
    cd ..
    goto end
)
if "%opt%"=="2" (
    call BUILD_NUITKA_NATIVE.bat
    goto end
)
if "%opt%"=="3" (
    call BUILD_PROTECTED_EXE.bat
    goto end
)

:end
echo.
echo Process complete.
pause
