import streamlit as st
st.set_page_config(page_title="הצעת מחיר", layout="centered")

import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os
import arabic_reshaper
from bidi.algorithm import get_display

# פונקציה לשינוי טקסט ל־RTL עם shaping
def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))

# ציור טקסט RTL ב־PDF
def draw_rtl(cnv, x, y, text, fontname='Alef', fontsize=12):
    cnv.setFont(fontname, fontsize)
    cnv.drawRightString(x, y, rtl(text))

# כותרת ראשית ב־UI
st.title("הצעת מחיר")

# איתור וטענת פונט עברי ל־PDF
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ttf_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith('.ttf')]
if ttf_files:
    font_file = os.path.join(BASE_DIR, ttf_files[0])
    try:
        pdfmetrics.registerFont(TTFont('Alef', font_file))
        pdf_font = 'Alef'
    except Exception:
        pdf_font = 'Helvetica'
else:
    pdf_font = 'Helvetica'

# טופס פרטי הלקוח
with st.form('customer_form'):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("שם הלקוח:")
        phone = st.text_input("טלפון:")
        address = st.text_area("כתובת:")
    with col2:
        offer_date = st.date_input("תאריך:", value=date.today())
        discount_pct = st.number_input("אחוז הנחה:", min_value=0.0, max_value=100.0, value=0.0)
    submitted = st.form_submit_button("אשר פרטי לקוח")

if submitted:
    st.success(f"פרטי הלקוח נקלטו: {name}, {phone}, {address}")

@st.cache_data
def load_catalog(uploaded) -> pd.DataFrame:
    df = pd.read_excel(uploaded, sheet_name='גיליון1', header=8, engine='openpyxl')
    df.columns = df.columns.str.strip()
    if "מס'" in df.columns:
        df.rename(columns={"מס'": "קטגוריה"}, inplace=True)
    for col in df.columns:
        if 'פריט' in col and col != 'הפריט':
            df.rename(columns={col: 'הפריט'}, inplace=True)
            break
    if 'סה"כ' in df.columns:
        df.rename(columns={'סה"כ': 'סהכ'}, inplace=True)
    return df

# העלאת קטלוג ובחירת מוצרים
uploaded_file = st.file_uploader("העלה קובץ קטלוג (Excel):", type=['xlsx'])
if uploaded_file:
    catalog = load_catalog(uploaded_file)
    cols = [c for c in ['קטגוריה','הערות','הפריט','מחיר יחידה'] if c in catalog.columns]
    st.subheader("קטלוג מוצרים")
    st.dataframe(catalog[cols])

    choice = st.multiselect(
        "בחר מוצרים:",
        options=catalog.index,
        format_func=lambda i: f"{catalog.at[i,'הפריט']} ({catalog.at[i,'קטגוריה']})"
    )

    if choice:
        order = catalog.loc[choice, ['הפריט','מחיר יחידה']].copy()
        for idx in choice:
            qty = st.number_input(f"כמות עבור {catalog.at[idx,'הפריט']}:", min_value=1, value=1, key=f"qty_{idx}")
            order.at[idx,'כמות'] = qty
        order['סהכ'] = order['מחיר יחידה'] * order['כמות']

        st.subheader("פרטי הזמנה")
        st.dataframe(order[['הפריט','כמות','מחיר יחידה','סהכ']])

        sub = order['סהכ'].sum()
        vat = sub * 0.17
        disc = (sub + vat) * (discount_pct/100)
        tot = sub + vat - disc

        # הצגת סכומים ב־UI
        st.markdown(f"**סכום ביניים:** {sub:.2f} ₪")
        st.markdown(f"**מע\"מ (17%):** {vat:.2f} ₪")
        st.markdown(f"**הנחה ({discount_pct}%):** -{disc:.2f} ₪")
        st.markdown(f"**סך הכל לתשלום:** {tot:.2f} ₪")

        # יצירת PDF
        if st.button("ייצא ל-PDF"):
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            c = canvas.Canvas(tmp_file.name, pagesize=A4)
            W, H = A4
            m = 20 * mm

            # לוגו
            logo_path = os.path.join(BASE_DIR, 'Logo.jpeg')
            if os.path.exists(logo_path):
                c.drawImage(logo_path, m, H - m - 40*mm, width=40*mm, preserveAspectRatio=True)

            # כותרת ופרטים
            draw_rtl(c, W - m, H - m, f"הצעת מחיר ל-{name}", fontsize=16)
            y = H - m - 50*mm
            draw_rtl(c, W - m, y, f"תאריך: {offer_date}", fontsize=12)
            y -= 6*mm
            draw_rtl(c, W - m, y, f"טלפון: {phone}", fontsize=12)
            y -= 6*mm
            draw_rtl(c, W - m, y, f"כתובת: {address}", fontsize=12)

            # טבלת מוצרים במבנה RTL
            y -= 20*mm
            draw_rtl(c, W - m, y, "סהכ", fontsize=12)
            draw_rtl(c, W - m - 50*mm, y, "מחיר ליחידה", fontsize=12)
            draw_rtl(c, m + 80*mm, y, "כמות", fontsize=12)
            draw_rtl(c, m, y, "מוצר", fontsize=12)
            y -= 6*mm
            for rec in order.to_dict(orient='records'):
                c.drawString(m, y, rec['הפריט'])
                c.drawRightString(m + 80*mm, y, str(int(rec['כמות'])))
                c.drawRightString(W - m - 50*mm, y, f"{rec['מחיר יחידה']:.2f}")
                c.drawRightString(W - m, y, f"{rec['סהכ']:.2f}")
                y -= 6*mm

            # סיכומים במבנה RTL: תווית ואז ערך
            y -= 10*mm
            draw_rtl(c, m + 20*mm, y, "סכום ביניים", fontsize=12)
            c.drawRightString(W - m, y, f"{sub:.2f}")
            y -= 6*mm
            draw_rtl(c, m + 20*mm, y, "מע\"מ (17%)", fontsize=12)
            c.drawRightString(W - m, y, f"{vat:.2f}")
            y -= 6*mm
            draw_rtl(c, m + 20*mm, y, f"הנחה ({discount_pct}%)", fontsize=12)
            c.drawRightString(W - m, y, f"-{disc:.2f}")
            y -= 6*mm
            draw_rtl(c, m + 20*mm, y, "סך הכל לתשלום", fontsize=12)
            c.drawRightString(W - m, y, f"{tot:.2f}")

            # Footer ושיפור מיקום החתימה
            y = m + 30*mm
            validity = (offer_date + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            draw_rtl(c, W - m, y + 10*mm, f"הצעה תקפה עד ל-{validity}", fontsize=10)
            draw_rtl(c, m, y, "חתימת הלקוח: ____________________________", fontsize=12)

            c.showPage()
            c.save()

            with open(tmp_file.name, 'rb') as f:
                pdf_bytes = f.read()
            st.download_button(
                label="הורד הצעת מחיר כ-PDF",
                data=pdf_bytes,
                file_name=f"offer_{name}_{offer_date}.pdf",
                mime='application/pdf'
            )
