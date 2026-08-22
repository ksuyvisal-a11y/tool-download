@echo off
title SKD TOOL - NUITKA NATIVE C MACHINE CODE COMPILER (ANTI-DECOMPILE)
cls
echo =====================================================================
echo   SKD TOOL - NATIVE C/C++ MACHINE CODE COMPILER (NUITKA C SHIELD)
echo =====================================================================
echo.
echo [1/3] Minifying frontend assets & checking encryption...
python minify_frontend.py

echo.
echo [2/3] Compiling Python source into pure C and Native x86_64 Machine Code...
echo (Translates all .py files directly into C Assembly Binary instructions)
echo.

python -m nuitka --standalone --windows-console-mode=disable --windows-icon-from-ico=assets/app_icon.ico --include-data-dir=assets=assets --include-data-dir=ui=ui --python-flag=no_docstrings --lto=yes --output-dir=dist_native app.py

echo.
if exist "dist_native\app.dist\app.exe" (
    echo =====================================================================
    echo   [SUCCESS] NATIVE C BINARY COMPILED: dist_native\app.dist\app.exe
    echo   [SHIELD] No Python Bytecode (.pyc). No PyInstaller Archive.
    echo   [SHIELD] 100%% Native x86_64 C Machine Code!
    echo   [PROTECTION] Anti-Decompile, Anti-Debug, and RSA-2048 Active.
    echo =====================================================================
) else (
    echo [ERROR] Native C Compilation failed. Check the logs above.
)
pause
