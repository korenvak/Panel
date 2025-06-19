import streamlit as st
import pandas as pd
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
from reportlab.lib.units import mm
# RTL support
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None
import tempfile
import os
import io
import base64

# הגדרות עמוד
st.set_page_config(
    page_title="Panel Kitchens - הצעות מחיר",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS מותאם אישית
st.markdown("""
<style>
    /* RTL support */
    .stApp {
        direction: rtl;
        text-align: right;
    }

    /* Header styling */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .logo-container {
        flex: 1;
        text-align: center;
    }

    .title-container {
        flex: 2;
        text-align: right;
    }

    h1 {
        color: #d32f2f;
        font-family: 'Heebo', sans-serif;
        margin: 0;
    }

    /* Table styling */
    .dataframe {
        text-align: right !important;
        direction: rtl !important;
    }

    /* Input styling */
    .stNumberInput > div > div > input {
        text-align: center;
        background-color: #f5f5f5;
    }

    .stNumberInput[value="0"] > div > div > input {
        background-color: white;
    }

    /* Button styling */
    .stButton > button {
        background-color: #d32f2f;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 2rem;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        background-color: #b71c1c;
        transform: scale(1.05);
    }

    /* Summary box */
    .summary-box {
        background-color: #f5f5f5;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #d32f2f;
        margin-top: 1rem;
    }

    /* File uploader */
    .stFileUploader {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 10px;
        border: 2px dashed #ff6f00;
    }

    /* Category header */
    .category-header {
        background-color: #d32f2f;
        color: white;
        padding: 0.5rem;
        margin: 1rem 0;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# פונקציה להיפוך טקסט עברי
def reverse_hebrew(text):
    """הפוך טקסט עברי לתצוגה נכונה"""
    if isinstance(text, str):
        # בדיקה אם הטקסט מכיל עברית
        if any('\u0590' <= char <= '\u05FF' for char in text):
            return text[::-1]
    return text

# פונקציה לתמיכה ב-RTL מלא
def rtl(text):
    """Reshape and bidi text for proper RTL display"""
    if not isinstance(text, str):
        text = str(text)
    if arabic_reshaper and get_display:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except Exception:
            pass
    return text[::-1]


# Header עם לוגו
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # בדיקה אם קיים לוגו
    logo_path = None
    for ext in ['png', 'jpg', 'jpeg']:
        if os.path.exists(f'logo.{ext}'):
            logo_path = f'logo.{ext}'
            break
        elif os.path.exists(f'Logo.{ext}'):
            logo_path = f'Logo.{ext}'
            break

    if logo_path:
        logo_col, title_col = st.columns([1, 3])
        with logo_col:
            st.image(logo_path, width=150)
        with title_col:
            st.markdown("""
            <div class="title-container">
                <h1>מערכת הצעות מחיר</h1>
                <p style="color: #666; margin: 0;">Panel Kitchens - מטבחים באיכות גבוהה</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <div class="title-container">
                <h1>מערכת הצעות מחיר</h1>
                <p style="color: #666; margin: 0;">Panel Kitchens - מטבחים באיכות גבוהה</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# אתחול session state
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = {
        'name': '',
        'phone': '',
        'address': '',
        'date': date.today(),
        'discount': 0.0,
        'contractor': False,
        'contractor_discount': 0.0
    }

if 'selected_items' not in st.session_state:
    st.session_state.selected_items = pd.DataFrame()

if 'demo1' not in st.session_state:
    st.session_state.demo1 = None
if 'demo2' not in st.session_state:
    st.session_state.demo2 = None


# פונקציה לטעינת קטלוג
@st.cache_data
def load_catalog(file):
    try:
        df = pd.read_excel(file, sheet_name='גיליון1', header=8, engine='openpyxl')
        df.columns = df.columns.str.strip()

        # שינוי שמות עמודות
        rename_dict = {
            "מס'": "מספר",
            'סה"כ': 'סהכ'
        }
        df.rename(columns=rename_dict, inplace=True)

        # חיפוש עמודת פריט
        for col in df.columns:
            if 'פריט' in col and col != 'הפריט':
                df.rename(columns={col: 'הפריט'}, inplace=True)
                break

        # הוספת עמודת כמות
        df['כמות'] = 0

        # הוספת עמודת קטגוריה
        df['קטגוריה'] = ''
        current_category = ''

        for idx in df.index:
            # בדיקה אם זו שורת קטגוריה (אין מחיר יחידה)
            if pd.isna(df.at[idx, 'מחיר יחידה']) or df.at[idx, 'מחיר יחידה'] == '':
                # זיהוי קטגוריה מהעמודה הראשונה שיש בה טקסט
                for col in df.columns:
                    if pd.notna(df.at[idx, col]) and str(df.at[idx, col]).strip() != '':
                        current_category = str(df.at[idx, col]).strip()
                        break
            else:
                df.at[idx, 'קטגוריה'] = current_category

        # סינון רק שורות עם מחיר יחידה
        df = df[pd.notna(df['מחיר יחידה'])].copy()

        # המרת מחיר יחידה למספר
        df['מחיר יחידה'] = pd.to_numeric(df['מחיר יחידה'], errors='coerce').fillna(0)

        # טיפול בעמודת הערות
        if 'הערות' not in df.columns:
            df['הערות'] = ''
        df['הערות'] = df['הערות'].fillna('')

        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ: {str(e)}")
        return None


# יצירת PDF משופר
def create_enhanced_pdf(customer_data, items_df, demo1=None, demo2=None):
    """יצירת PDF עם עיצוב משופר"""
    buffer = io.BytesIO()

    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    m = 20 * mm
    ROW_HEIGHT = 6 * mm

    # רישום גופנים
    try:
        reg_path = os.path.join(os.path.dirname(__file__), 'Heebo-Regular.ttf')
        bold_path = os.path.join(os.path.dirname(__file__), 'Heebo-Bold.ttf')
        pdfmetrics.registerFont(TTFont('Heebo', reg_path))
        pdfmetrics.registerFont(TTFont('Heebo-Bold', bold_path))
        PDF_FONT = 'Heebo'
        PDF_BOLD = 'Heebo-Bold'
    except Exception:
        font_path = os.path.join(os.path.dirname(__file__), 'Alef Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Hebrew', font_path))
            PDF_FONT = 'Hebrew'
            PDF_BOLD = 'Hebrew'
        else:
            PDF_FONT = PDF_BOLD = 'Helvetica'

    def draw_rtl(canv, x, y, text, font=PDF_FONT, fontsize=12):
        canv.setFont(font, fontsize)
        canv.drawRightString(x, y, rtl(text))

    def draw_watermark(canv):
        wm_path = 'watermark.png'
        if os.path.exists(wm_path):
            canv.saveState()
            try:
                canv.setFillAlpha(0.1)
            except Exception:
                pass
            img = ImageReader(wm_path)
            w_img, h_img = img.getSize()
            scale = min((W / 2) / w_img, (H / 2) / h_img)
            nw, nh = w_img * scale, h_img * scale
            canv.translate(W / 2, H / 2)
            canv.rotate(45)
            canv.drawImage(img, -nw / 2, -nh / 2, width=nw, height=nh)
            canv.restoreState()

    def draw_footer(canv, page, total):
        canv.setFillColorRGB(0.827, 0.184, 0.184)
        canv.rect(0, 0, W, 3 * mm, fill=1, stroke=0)
        x = m
        logo_small = 'logo_small.png'
        if os.path.exists(logo_small):
            canv.drawImage(logo_small, x, 3 * mm, height=5 * mm, preserveAspectRatio=True)
            x += 20 * mm
        canv.setFont(PDF_FONT, 8)
        canv.setFillColorRGB(0, 0, 0)
        canv.drawString(x, 5 * mm, 'Panel Kitchens | www.panel-k.co.il | טל: 072-393-3997')
        draw_rtl(canv, W - m, 5 * mm, f"עמוד {page} מתוך {total}", PDF_FONT, 8)
        link_text = rtl("לחזור לדשבורד")
        link_w = pdfmetrics.stringWidth(link_text, PDF_FONT, 8)
        canv.drawString(W - m - link_w, 10 * mm, link_text)
        try:
            from reportlab.pdfbase.pdfdoc import PDFAnnotation
            annot = PDFAnnotation(uri="https://dashboard.url", Rect=(W - m - link_w, 10 * mm, W - m, 14 * mm), Subtype='Link')
            canv._addAnnotation(annot)
        except Exception:
            pass

    pages_total = 2 + (1 if (demo1 or demo2) else 0)
    page_num = 1

    # עמוד שער
    cover_bar = 'cover_bar.png'
    if os.path.exists(cover_bar):
        c.saveState()
        try:
            c.setFillAlpha(0.3)
        except Exception:
            pass
        c.drawImage(cover_bar, 0, H - 30 * mm, width=W, height=30 * mm)
        c.restoreState()

    big_logo = 'logo_big.png'
    if os.path.exists(big_logo):
        c.drawImage(big_logo, (W - 100 * mm) / 2, H - 70 * mm, width=100 * mm, preserveAspectRatio=True)

    c.setFont(PDF_BOLD, 36)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.drawCentredString(W / 2, H - 90 * mm, rtl('הצעת מחיר'))
    c.setFillColorRGB(0, 0, 0)
    draw_rtl(c, W - m, H - 110 * mm, f"לכבוד: {customer_data['name']} | תאריך: {customer_data['date'].strftime('%d/%m/%Y')}", PDF_FONT, fontsize=18)
    draw_watermark(c)
    draw_footer(c, page_num, pages_total)
    c.showPage()
    page_num += 1

    # עמוד נתונים
    logo_path = None
    for ext in ['png', 'jpg', 'jpeg']:
        if os.path.exists(f'logo.{ext}'):
            logo_path = f'logo.{ext}'
            break
        elif os.path.exists(f'Logo.{ext}'):
            logo_path = f'Logo.{ext}'
            break

    if logo_path:
        try:
            img = PILImage.open(logo_path).convert("RGBA")
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            temp_logo = os.path.join(tempfile.gettempdir(), "logo_flat.jpg")
            bg.save(temp_logo)
            logo_flat = ImageReader(temp_logo)
            c.drawImage(logo_flat, m, H - m - 40 * mm, 40 * mm, preserveAspectRatio=True)
        except Exception as e:
            print(f"Error loading logo: {e}")

    draw_watermark(c)
    y = H - 40 * mm
    c.setFont(PDF_FONT, 24)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.drawCentredString(W / 2, y, rtl('הצעת מחיר'))

    y -= 20 * mm
    c.setFillColorRGB(0, 0, 0)
    draw_rtl(c, W - m, y, f"לכבוד: {customer_data['name']}", PDF_FONT, fontsize=12)
    draw_rtl(c, W - m, y - 6 * mm, f"תאריך: {customer_data['date'].strftime('%d/%m/%Y')}", PDF_FONT, fontsize=12)
    draw_rtl(c, W - m, y - 12 * mm, f"טלפון: {customer_data['phone']}", PDF_FONT, fontsize=12)
    draw_rtl(c, W - m, y - 18 * mm, f'דוא"ל: {customer_data["email"]}', PDF_FONT, fontsize=12)
    draw_rtl(c, W - m, y - 24 * mm, f"כתובת: {customer_data['address']}", PDF_FONT, fontsize=12)
    y -= 30 * mm

    c.setFont(PDF_FONT, 11)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1)
    c.setFillColorRGB(1, 1, 1)
    headers = [
        ("מוצר", W - m),
        ("כמות", W - m - 40 * mm),
        ("מחיר ליחידה", W - m - 80 * mm),
        ("סה\"כ", W - m - 120 * mm),
    ]
    for text, pos in headers:
        draw_rtl(c, pos, y, text, PDF_FONT, fontsize=11)

    y -= ROW_HEIGHT
    c.setFont(PDF_FONT, 10)
    c.setFillColorRGB(0, 0, 0)
    for i, rec in enumerate(items_df.to_dict(orient='records')):
        if i % 2 == 0:
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        draw_rtl(c, W - m, y, rec['הפריט'], PDF_FONT, 10)
        c.drawRightString(W - m - 40 * mm, y, str(int(rec['כמות'])))
        c.drawRightString(W - m - 80 * mm, y, f"₪{rec['מחיר יחידה']:.2f}")
        c.drawRightString(W - m - 120 * mm, y, f"₪{rec['סהכ']:.2f}")
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=0, stroke=1)
        y -= ROW_HEIGHT

    y -= 20 * mm
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.827, 0.184, 0.184)
    c.line(m, y, W - m, y)

    y -= 10 * mm
    c.setFont(PDF_FONT, 12)
    subtotal = items_df['סהכ'].sum()
    contractor_discount = float(customer_data.get('contractor_discount', 0))
    sub_after = subtotal - contractor_discount
    vat = sub_after * 0.17
    discount_amount = (sub_after + vat) * (customer_data['discount'] / 100)
    total = sub_after + vat - discount_amount

    summary_lines = []
    if contractor_discount:
        summary_lines.append((rtl("הנחת קבלן"), f"-₪{contractor_discount:,.2f}"))
    summary_lines.extend([
        (rtl("סכום ביניים"), f"₪{sub_after:,.2f}"),
        (rtl('מע"מ (17%)'), f"₪{vat:,.2f}"),
        (rtl(f"הנחה ({customer_data['discount']}%)"), f"-₪{discount_amount:,.2f}")
    ])
    for label, value in summary_lines:
        c.drawRightString(W - m, y, label)
        c.drawRightString(W - m - 60 * mm, y, value)
        y -= 6 * mm

    c.setFont(PDF_FONT, 12)
    c.setFillColorRGB(1, 0, 0)
    draw_rtl(c, W - m, y, "סך הכל לתשלום", PDF_FONT, 12)
    c.drawRightString(W - m - 60 * mm, y, f"₪{total:,.2f}")
    c.setFillColorRGB(0, 0, 0)

    draw_footer(c, page_num, pages_total)
    c.showPage()
    page_num += 1

    if demo1 or demo2:
        draw_watermark(c)
        y_img = H - m
        if demo1:
            c.setFont(PDF_FONT, 24)
            c.drawCentredString(W / 2, y_img, rtl("הדמיה"))
            y_img -= 10 * mm
            img1 = ImageReader(demo1)
            w1, h1 = img1.getSize()
            max_w = W - 40 * mm
            max_h = (H / 2 - 40 * mm) if demo2 else H - 40 * mm
            r1 = min(max_w / w1, max_h / h1)
            nw1, nh1 = w1 * r1, h1 * r1
            x1 = (W - nw1) / 2
            c.drawImage(img1, x1, y_img - nh1, width=nw1, height=nh1)
            y_img = y_img - nh1 - 20 * mm
        if demo2:
            c.setFont(PDF_FONT, 24)
            c.drawCentredString(W / 2, y_img, rtl("הדמיית נקודות מים וחשמל"))
            y_img -= 10 * mm
            img2 = ImageReader(demo2)
            w2, h2 = img2.getSize()
            max_w = W - 40 * mm
            max_h = H / 2 - 40 * mm if demo1 else H - 40 * mm
            r2 = min(max_w / w2, max_h / h2)
            nw2, nh2 = w2 * r2, h2 * r2
            x2 = (W - nw2) / 2
            c.drawImage(img2, x2, y_img - nh2, width=nw2, height=nh2)

    y = H - 30 * mm
    c.setFont(PDF_FONT, 8)
    for t in [
        "הצעת המחיר תקפה ל-14 ימים ממועד הפקתה.",
        "ההצעה מיועדת ללקוח הספציפי בלבד ולא להעברה לחוץ.",
        "המחירים עשויים להשתנות והחברה אינה אחראית לטעויות.",
        "אישור ההצעה מהווה התחייבות לתשלום 10% מקדמה.",
        "הלקוח מתחייב לפנות נקודות מים וחשמל בהתאם לתכניות.",
        "אי עמידה בתנאים עלולה לגרור עיכובים וחריגות."
    ]:
        draw_rtl(c, W - m, y, t, PDF_FONT, 8)
        y -= 4 * mm
    y -= 8 * mm
    if y < 30 * mm:
        y = 30 * mm
    draw_rtl(c, W - m, y, "חתימת הלקוח: ____________________", PDF_FONT, 12)

    c.setFont(PDF_FONT, 10)
    c.drawString(m, 20 * mm, rtl("הנגרים 1 (מתחם הורדוס), באר שבע"))
    c.drawString(m, 15 * mm, rtl("טל: 072-393-3997"))
    c.drawString(m, 10 * mm, rtl("דוא\"ל: M@panel-k.co.il"))
    draw_footer(c, page_num, pages_total)
    c.showPage()
    page_num += 1

    c.save()
    buffer.seek(0)
    return buffer


# ממשק משתמש ראשי
tab1, tab2, tab3 = st.tabs(["📝 פרטי לקוח", "🛒 בחירת מוצרים", "📄 יצירת הצעה"])

# טאב 1: פרטי לקוח
with tab1:
    st.subheader("הזן פרטי לקוח")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.customer_data['name'] = st.text_input(
            "שם הלקוח:",
            value=st.session_state.customer_data['name'],
            placeholder="הזן שם מלא"
        )
        st.session_state.customer_data['phone'] = st.text_input(
            "טלפון:",
            value=st.session_state.customer_data['phone'],
            placeholder="050-1234567"
        )

    with col2:
        st.session_state.customer_data['date'] = st.date_input(
            "תאריך:",
            value=st.session_state.customer_data['date']
        )
        st.session_state.customer_data['discount'] = st.number_input(
            "אחוז הנחה:",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.customer_data['discount'],
            step=5.0
        )
        st.session_state.customer_data['contractor'] = st.checkbox(
            "הנחת קבלן",
            value=st.session_state.customer_data.get('contractor', False)
        )
        if st.session_state.customer_data['contractor']:
            st.session_state.customer_data['contractor_discount'] = st.number_input(
                "סכום הנחת קבלן (₪):",
                min_value=0.0,
                value=st.session_state.customer_data.get('contractor_discount', 0.0),
                step=100.0,
                format="%.2f"
            )
        else:
            st.session_state.customer_data['contractor_discount'] = 0.0

    st.session_state.customer_data['address'] = st.text_area(
        "כתובת:",
        value=st.session_state.customer_data['address'],
        placeholder="רחוב, מספר, עיר",
        height=100
    )

# טאב 2: בחירת מוצרים
with tab2:
    st.subheader("בחר מוצרים מהקטלוג")

    # העלאת קובץ עם drag & drop
    uploaded_file = st.file_uploader(
        "גרור קובץ קטלוג לכאן או לחץ לבחירה",
        type=['xlsx', 'xls'],
        help="קובץ Excel עם רשימת המוצרים"
    )

    if uploaded_file:
        catalog_df = load_catalog(uploaded_file)

        if catalog_df is not None:
            st.success("הקטלוג נטען בהצלחה!")

            # הצגת טבלה עם אפשרות עריכה
            st.markdown("### רשימת מוצרים - הזן כמות ליד כל מוצר")

            # יצירת עותק לעריכה
            edited_df = catalog_df.copy()

            # קיבוץ לפי קטגוריות
            categories = edited_df['קטגוריה'].unique()

            for category in categories:
                if category:  # רק אם יש קטגוריה
                    st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)

                category_df = edited_df[edited_df['קטגוריה'] == category]

                # הצגת טבלה בלולאה עם input לכמות
                for idx in category_df.index:
                    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1, 1, 1])

                    with col1:
                        st.write(edited_df.at[idx, 'הפריט'])
                    with col2:
                        st.write(edited_df.at[idx, 'הערות'])
                    with col3:
                        price = edited_df.at[idx, 'מחיר יחידה']
                        if pd.notna(price) and price != 0:
                            st.write(f"₪{price:,.0f}")
                        else:
                            st.write("לפי מידה")
                    with col4:
                        qty = st.number_input(
                            "כמות",
                            min_value=0,
                            value=0,
                            step=1,
                            key=f"qty_{idx}",
                            label_visibility="collapsed"
                        )
                        edited_df.at[idx, 'כמות'] = qty
                    with col5:
                        if qty > 0 and pd.notna(price) and price != 0:
                            total = qty * price
                            st.write(f"₪{total:,.0f}")
                            edited_df.at[idx, 'סהכ'] = total
                        else:
                            st.write("-")
                            edited_df.at[idx, 'סהכ'] = 0

            # סינון רק פריטים שנבחרו
            selected_df = edited_df[edited_df['כמות'] > 0].copy()

            if not selected_df.empty:
                st.session_state.selected_items = selected_df

                # הצגת סיכום
                st.markdown("### סיכום הזמנה")
                display_columns = ['הפריט', 'הערות', 'כמות', 'מחיר יחידה', 'סהכ']
                st.dataframe(
                    selected_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )

                # חישוב סכומים
                subtotal = selected_df['סהכ'].sum()
                vat = subtotal * 0.17
                discount = (subtotal + vat) * (st.session_state.customer_data['discount'] / 100)
                total = subtotal + vat - discount

                # תיבת סיכום
                st.markdown(f"""
                <div class="summary-box">
                    <h4>סיכום תשלום:</h4>
                    <p>סכום ביניים: <b>₪{subtotal:,.2f}</b></p>
                    <p>מע"מ (17%): <b>₪{vat:,.2f}</b></p>
                    <p>הנחה ({st.session_state.customer_data['discount']}%): <b>-₪{discount:,.2f}</b></p>
                    <hr>
                    <h3>סך הכל לתשלום: <span style="color: #d32f2f;">₪{total:,.2f}</span></h3>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("לא נבחרו מוצרים עדיין. הזן כמות ליד המוצרים הרצויים.")

# טאב 3: יצירת הצעה
with tab3:
    st.subheader("יצירת הצעת מחיר")

    # בדיקת נתונים
    if not st.session_state.customer_data['name']:
        st.warning("יש להזין פרטי לקוח בטאב הראשון")
    elif isinstance(st.session_state.selected_items, pd.DataFrame) and st.session_state.selected_items.empty:
        st.warning("יש לבחור מוצרים בטאב השני")
    else:
        # אפשרות להוסיף הדמיה
        st.markdown("### הוסף הדמיה (אופציונלי)")
        demo_file = st.file_uploader(
            "גרור תמונת הדמיה לכאן או לחץ לבחירה",
            type=['png', 'jpg', 'jpeg'],
            help="התמונה תתווסף כעמוד נפרד ב-PDF",
        )

        if demo_file:
            st.session_state.demo1 = demo_file
            st.success("ההדמיה נוספה בהצלחה!")
            st.image(demo_file, caption="תצוגה מקדימה של ההדמיה", use_column_width=True)

        demo2_file = st.file_uploader(
            "גרור הדמיית נקודות מים/חשמל",
            type=['png', 'jpg', 'jpeg'],
            help="תמונה זו תתווסף כעמוד נפרד ב-PDF",
            key="demo2_upload",
        )

        if demo2_file:
            st.session_state.demo2 = demo2_file
            st.success("הדמיה נוספת נוספה בהצלחה!")
            st.image(demo2_file, caption="תצוגה מקדימה של הדמיה נוספת", use_column_width=True)

        # כפתור יצירת PDF
        if st.button("🎯 צור הצעת מחיר", type="primary", use_container_width=True):
            with st.spinner("יוצר הצעת מחיר..."):
                # יצירת PDF
                pdf_buffer = create_enhanced_pdf(
                    st.session_state.customer_data,
                    st.session_state.selected_items,
                    st.session_state.demo1,
                    st.session_state.demo2
                )

                # הורדת קובץ
                st.success("ההצעה נוצרה בהצלחה!")
                st.download_button(
                    label="📥 הורד הצעת מחיר",
                    data=pdf_buffer,
                    file_name=f"הצעת_מחיר_{st.session_state.customer_data['name']}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                # אפשרות לאפס
                if st.button("🔄 התחל הצעה חדשה", use_container_width=True):
                    for key in st.session_state.keys():
                        del st.session_state[key]
                    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #999;">
        <p>Panel Kitchens © 2025 | מערכת הצעות מחיר</p>
    </div>
    """,
    unsafe_allow_html=True
)
