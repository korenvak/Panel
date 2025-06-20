import os
import shutil
from PIL import Image, ImageDraw

print("Creating missing files...")

# Create .streamlit directory and config
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
print("✓ Created .streamlit/config.toml")

# Create watermark.png if it doesn't exist
if not os.path.exists('assets/watermark.png'):
    # Create a simple watermark image
    img = Image.new('RGBA', (400, 100), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    # Just save a transparent image - won't show anything but prevents errors
    img.save('assets/watermark.png')
    print("✓ Created assets/watermark.png (transparent placeholder)")

# Handle missing font - copy Regular as Bold if Bold doesn't exist
if not os.path.exists('assets/Heebo-Bold.ttf'):
    if os.path.exists('assets/Heebo-Regular.ttf'):
        shutil.copy('assets/Heebo-Regular.ttf', 'assets/Heebo-Bold.ttf')
        print("✓ Created assets/Heebo-Bold.ttf (copied from Regular)")
    else:
        print("✗ Cannot create Heebo-Bold.ttf - Regular font not found")

print("\nDone! You can now run build_exe.py")