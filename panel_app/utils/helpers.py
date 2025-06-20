# file: panel_app/utils/helpers.py
import os
import sys


def get_base_path() -> str:
    """Return base path, compatible with PyInstaller executables."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(__file__))


BASE_DIR = get_base_path()
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def asset_path(filename: str) -> str:
    """Return absolute path for file inside the assets directory."""
    return os.path.join(ASSETS_DIR, filename)
