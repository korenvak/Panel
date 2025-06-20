# file: panel_app/app.py
import os
import sys
import streamlit as st

# Add the current directory to Python path for imports
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    base_path = sys._MEIPASS
else:
    # Running in normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))

# Add base path to sys.path so imports work
if base_path not in sys.path:
    sys.path.insert(0, base_path)

from dashboard import render_dashboard

st.set_page_config(
    page_title="Panel Kitchens - הצעות מחיר",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Handle CSS file path
css_file = os.path.join(base_path, 'static', 'custom.css')
if os.path.exists(css_file):
    with open(css_file, encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_dashboard()