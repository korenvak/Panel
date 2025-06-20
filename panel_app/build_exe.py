import PyInstaller.__main__
import os
import shutil
import sys

# Clean previous builds
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# Prepare data files list
data_files = [
    # Python files
    'app.py;.',
    'dashboard.py;.',
    'catalog_loader.py;.',
    'pdf_generator.py;.',
    'utils/helpers.py;utils',
    'utils/rtl.py;utils',
    # Static files
    'static/custom.css;static',
]

# Add asset files if they exist
asset_extensions = ['.png', '.ico', '.ttf', '.jpg', '.jpeg']
if os.path.exists('assets'):
    for file in os.listdir('assets'):
        if any(file.endswith(ext) for ext in asset_extensions):
            data_files.append(f'assets/{file};assets')

# Add streamlit config if it exists
if os.path.exists('.streamlit/config.toml'):
    data_files.append('.streamlit/config.toml;.streamlit')
else:
    print("Warning: .streamlit/config.toml not found. Creating it now...")
    os.makedirs('.streamlit', exist_ok=True)
    with open('.streamlit/config.toml', 'w') as f:
        f.write("""[global]
developmentMode = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[runner]
magicEnabled = false

[client]
showErrorDetails = false
""")
    data_files.append('.streamlit/config.toml;.streamlit')

# Build arguments for PyInstaller
args = [
    'run_app.py',
    '--onefile',
    '--name=PanelKitchens',
    '--console',  # Keep console for debugging
    '--clean',
    '--noconfirm',
]

# Add icon if it exists
if os.path.exists('assets/White_Logo.ico'):
    args.append('--icon=assets/White_Logo.ico')

# Add all data files
for data_file in data_files:
    args.append(f'--add-data={data_file}')

# Add hidden imports
hidden_imports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.config',
    'pandas',
    'openpyxl',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.utils',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    'reportlab.pdfbase',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase.pdfmetrics',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'arabic_reshaper',
    'bidi',
    'bidi.algorithm',
    'altair',
    'pyarrow',
    'validators',
    'watchdog',
    'tornado',
    'numpy',
    'pytz',
    'tzlocal',
    'packaging',
    'toml',
    'click',
    'pympler',
    'backports.zoneinfo',
]

for import_name in hidden_imports:
    args.append(f'--hidden-import={import_name}')

# Collect all data from streamlit and reportlab
args.append('--collect-all=streamlit')
args.append('--collect-all=reportlab')
args.append('--collect-all=PIL')

# Print the command for debugging
print("Running PyInstaller with the following arguments:")
print(" ".join(args))
print()

# Run PyInstaller
try:
    PyInstaller.__main__.run(args)
    print("\nBuild complete! Check the 'dist' folder for your executable.")
except Exception as e:
    print(f"\nBuild failed with error: {e}")
    sys.exit(1)