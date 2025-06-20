import os

print("Checking project files...")
print(f"Current directory: {os.getcwd()}")
print()

# Files to check
files_to_check = [
    'run_app.py',
    'app.py',
    'dashboard.py',
    'catalog_loader.py',
    'pdf_generator.py',
    'utils/helpers.py',
    'utils/rtl.py',
    'static/custom.css',
    'assets/logo.png',
    'assets/White_Logo.png',
    'assets/White_Logo.ico',
    'assets/watermark.png',
    'assets/Heebo-Regular.ttf',
    'assets/Heebo-Bold.ttf',
    '.streamlit/config.toml',
]

missing_files = []
for file in files_to_check:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MISSING")
        missing_files.append(file)

print()
if missing_files:
    print("Missing files:")
    for file in missing_files:
        print(f"  - {file}")
    print("\nPlease ensure all files are in place before building.")
else:
    print("All files found! Ready to build.")