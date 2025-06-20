# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('app.py', '.'), ('dashboard.py', '.'), ('catalog_loader.py', '.'), ('pdf_generator.py', '.'), ('utils/helpers.py', 'utils'), ('utils/rtl.py', 'utils'), ('static/custom.css', 'static'), ('assets/Heebo-Bold.ttf', 'assets'), ('assets/Heebo-Regular.ttf', 'assets'), ('assets/logo.png', 'assets'), ('assets/watermark.png', 'assets'), ('assets/White_Logo.ico', 'assets'), ('assets/White_Logo.png', 'assets'), ('.streamlit/config.toml', '.streamlit')]
binaries = []
hiddenimports = ['streamlit', 'streamlit.web.cli', 'streamlit.config', 'pandas', 'openpyxl', 'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes', 'reportlab.lib.units', 'reportlab.lib.utils', 'reportlab.pdfgen', 'reportlab.pdfgen.canvas', 'reportlab.pdfbase', 'reportlab.pdfbase.ttfonts', 'reportlab.pdfbase.pdfmetrics', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'arabic_reshaper', 'bidi', 'bidi.algorithm', 'altair', 'pyarrow', 'validators', 'watchdog', 'tornado', 'numpy', 'pytz', 'tzlocal', 'packaging', 'toml', 'click', 'pympler', 'backports.zoneinfo']
tmp_ret = collect_all('streamlit')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('reportlab')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PIL')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='PanelKitchens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\White_Logo.ico'],
)
