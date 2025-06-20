# file: panel_app/utils/helpers.py
import os
import sys


def get_base_path() -> str:
    """Return base path, compatible with PyInstaller executables."""
    if getattr(sys, "frozen", False):
        # Running in PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running in normal Python environment
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_path()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def asset_path(filename: str) -> str:
    """Return absolute path for file inside the assets directory."""
    path = os.path.join(ASSETS_DIR, filename)
    # Debug print for troubleshooting
    if not os.path.exists(path):
        print(f"Warning: Asset not found at {path}")
    return path