from PIL import Image
import os

# נתיב לתמונת המקור
src_path = os.path.join('assets', 'White_Logo.png')

# נתיב לשמירת קובץ ה‑ICO
dst_path = os.path.join('assets', 'White_Logo.ico')

# טוענים את התמונה עם תמיכה בשקיפות
img = Image.open(src_path).convert("RGBA")

# נגדיר את הגדלים השונים שנרצה לכלול בקובץ ה‑ICO
# (בדרך כלל 256x256, 128x128, 64x64, 48x48, 32x32, 16x16)
sizes = [
    (256, 256),
    (128, 128),
    (64, 64),
    (48, 48),
    (32, 32),
    (16, 16),
]

# שומרים כ‑ICO עם כל הגדלים הנ״ל
img.save(dst_path, format='ICO', sizes=sizes)

print(f"Saved ICO to {dst_path}")
