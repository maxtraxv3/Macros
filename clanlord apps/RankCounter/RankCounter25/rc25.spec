# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rc25.py'],
    pathex=[],
    binaries=[],
    datas=[('rankmessages.txt', '.'), ('trainers.txt', '.'), ('specialphrases.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rc25',
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
    icon=['C:\\Users\\user\\Desktop\\Macros\\clanlord apps\\RankCounter\\RankCounter25\\portal.png'],
)
