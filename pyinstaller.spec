# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

hidden_streamlit = collect_submodules("streamlit")
data_streamlit = collect_data_files("streamlit") + copy_metadata("streamlit")

a = Analysis(
    ['run_app.py'],
    pathex=['panel_app'],
    binaries=[],
    datas=data_streamlit + [
        ('panel_app/assets/*', 'assets'),
        ('panel_app/static/*', 'static'),
        ('panel_app/*.py', '.'),
        ('panel_app/utils/*.py', 'utils'),
    ],
    hiddenimports=hidden_streamlit + [
        'pandas',
        'openpyxl',
        'reportlab',
        'PIL',
        'arabic_reshaper',
        'bidi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Panel_Kitchens',
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
    icon='panel_app/assets/White_Logo.ico'
)
