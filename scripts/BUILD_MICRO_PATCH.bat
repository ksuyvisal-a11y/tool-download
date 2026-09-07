@echo off
title SKD TOOL - Build Micro-Patch (1MB Update)
color 0A
cd /d "%~dp0\.."

echo ===============================================================================
echo                SKD TOOL - 1-CLICK MICRO-PATCH BUILDER
echo              Creates Ultra-Lightweight (800KB - 1.5MB) Update ZIP
echo ===============================================================================
echo.

python build_micro_patch.py

echo.
echo ===============================================================================
echo  BUILD FINISHED!
echo  Opening 'dist' folder...
echo ===============================================================================
explorer dist
pause
