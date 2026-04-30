# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — URANNIO Finanças (app principal)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'anthropic',
        'anthropic._streaming',
        'firebase_admin',
        'firebase_admin.credentials',
        'firebase_admin.firestore',
        'google.cloud.firestore',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtCharts',
        'PyQt6.QtPrintSupport',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_agg',
        'numpy',
        'numpy.core',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
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
    name='URANNIO',
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
    icon=None,
)
