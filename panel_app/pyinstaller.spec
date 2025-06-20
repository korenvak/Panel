# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('dashboard.py', '.'),
        ('catalog_loader.py', '.'),
        ('pdf_generator.py', '.'),
        ('utils/*.py', 'utils'),
        ('assets/*', 'assets'),
        ('static/*', 'static'),
        ('.streamlit/config.toml', '.streamlit'),  # Include config file
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.config',
        'pandas',
        'openpyxl',
        'reportlab',
        'PIL',
        'arabic_reshaper',
        'bidi',
        'click',
        'altair',
        'pyarrow',
        'validators',
        'watchdog',
        'tornado',
        'pympler',
        'numpy',
        'pytz',
        'tzlocal',
        'packaging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='PanelKitchens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep as True for debugging, change to False when it works
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/White_Logo.ico',  # Use your icon file
)