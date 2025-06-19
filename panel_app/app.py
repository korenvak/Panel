# file: panel_app/app.py
import os
import streamlit as st

from dashboard import render_dashboard

st.set_page_config(
    page_title="Panel Kitchens - הצעות מחיר",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

css_file = os.path.join(os.path.dirname(__file__), 'static', 'custom.css')
with open(css_file, encoding='utf-8') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

render_dashboard()
