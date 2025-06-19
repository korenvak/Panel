# file: panel_app/utils/helpers.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')


def asset_path(filename: str) -> str:
    """Return absolute path for file inside the assets directory"""
    return os.path.join(ASSETS_DIR, filename)
