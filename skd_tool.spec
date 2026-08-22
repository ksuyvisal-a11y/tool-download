# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data and submodules for customtkinter, pywebview, and yt_dlp
datas = [
    ('assets', 'assets'),
    ('ui', 'ui'),
]
datas += collect_data_files('customtkinter')
datas += collect_data_files('webview')

hiddenimports = [
    'webview',
    'clr',
    'pythonnet',
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'yt_dlp',
    'imageio_ffmpeg',
    'requests',
    'urllib3',
    'certifi',
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'security_guard',
    'licensing',
    'downloader',
    'updater',
    'utils',
]
hiddenimports += collect_submodules('webview')
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('yt_dlp')

a = Analysis(
    ['armored_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'IPython', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SKD_TOOL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/app_icon.ico'],
)
