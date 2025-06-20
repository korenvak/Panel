# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata
from PyInstaller.building.build_main import Analysis, PYZ, EXE

# Use cwd() instead of __file__
here = os.getcwd()

# Collect everything Streamlit needs
hidden_streamlit = collect_submodules("streamlit")
data_streamlit = collect_data_files("streamlit") + copy_metadata("streamlit")

a = Analysis(
    [os.path.join(here, 'run_app.py')],
    pathex=[here],
    binaries=[],
    datas=(
        data_streamlit
        + [(os.path.join(here, 'assets', '*'), 'assets'),
           (os.path.join(here, 'static', '*'), 'static'),
           (os.path.join(here, '*.py'), '.'),
           (os.path.join(here, 'utils', '*.py'), 'utils')]
    ),
    hiddenimports=hidden_streamlit + [
        'pandas',
        'openpyxl',
        'reportlab',
        'PIL',
        'arabic_reshaper',
        'bidi.algorithm',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Panel_Kitchens',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(here, 'assets', 'White_Logo.ico'),
)
