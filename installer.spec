# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — URANNIO Instalador Interativo
# ATENÇÃO: execute APÓS urannio.spec ter gerado dist/URANNIO.exe

block_cipher = None

a = Analysis(
    ['installer_wizard.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Inclui o app compilado dentro do instalador
        ('dist/URANNIO.exe', '.'),
    ],
    hiddenimports=[
        'animated_logo',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'winreg',
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
    name='URANNIO_Setup_v1.0',
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
