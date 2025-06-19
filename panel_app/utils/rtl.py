# file: panel_app/utils/rtl.py
import arabic_reshaper
from bidi.algorithm import get_display

def reverse_hebrew(text: str) -> str:
    """Reverse Hebrew text for proper display"""
    if isinstance(text, str):
        if any('\u0590' <= char <= '\u05FF' for char in text):
            return text[::-1]
    return text

def rtl(text: str) -> str:
    """Reshape and apply bidi algorithm"""
    if not isinstance(text, str):
        text = str(text)
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text[::-1]
