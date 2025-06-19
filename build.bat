@echo off
echo Building Panel Kitchens EXE...

REM install dependencies
pip install -r requirements.txt

REM build the EXE
pyinstaller panel_app.spec --clean

echo Build complete!
pause
