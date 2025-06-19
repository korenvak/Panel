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
        'discount': 0.0
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
    width, height = A4

    try:
        font_path = os.path.join(os.path.dirname(__file__), 'Alef-Regular.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Hebrew', font_path))
            hebrew_font = 'Hebrew'
        else:
            try:
                pdfmetrics.registerFont(TTFont('Hebrew', 'C:/Windows/Fonts/Arial.ttf'))
                hebrew_font = 'Hebrew'
            except Exception:
                hebrew_font = 'Helvetica'
    except Exception:
        hebrew_font = 'Helvetica'

    # עמוד ראשון - הצעת מחיר
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
            logo = ImageReader(logo_path)
            c.drawImage(logo, width - 150, height - 100, width=100, height=50, preserveAspectRatio=True)
        except Exception as e:
            print(f"Error loading logo: {e}")

    y = height - 80
    c.setFont(hebrew_font, 24)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.drawCentredString(width / 2, y, rtl("הצעת מחיר"))

    y -= 60
    c.setFont(hebrew_font, 12)
    c.setFillColorRGB(0, 0, 0)
    details = [
        (rtl("לכבוד:"), rtl(customer_data.get('name', ''))),
        (rtl("תאריך:"), customer_data['date'].strftime('%d/%m/%Y')),
        (rtl("טלפון:"), customer_data.get('phone', '')),
        (rtl("כתובת:"), rtl(customer_data.get('address', '')))
    ]
    for label, value in details:
        c.drawRightString(width - 50, y, f"{label} {value}")
        y -= 20

    y -= 30
    c.setFont(hebrew_font, 11)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.rect(50, y - 15, width - 100, 25, fill=1)
    c.setFillColorRGB(1, 1, 1)
    headers = [
        (rtl("מוצר"), 450),
        (rtl("כמות"), 250),
        (rtl("מחיר ליחידה"), 150),
        (rtl('סה"כ'), 70)
    ]
    for text, pos in headers:
        c.drawRightString(pos, y, text)

    y -= 30
    c.setFont(hebrew_font, 10)
    c.setFillColorRGB(0, 0, 0)
    for idx, row in items_df.iterrows():
        if idx % 2 == 0:
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(50, y - 15, width - 100, 20, fill=1)
            c.setFillColorRGB(0, 0, 0)
        c.drawRightString(450, y, rtl(str(row['הפריט'])))
        c.drawRightString(250, y, str(int(row['כמות'])))
        c.drawRightString(150, y, f"₪{row['מחיר יחידה']:,.0f}")
        c.drawRightString(70, y, f"₪{row['סהכ']:,.0f}")
        y -= 25
        if y < 150:
            c.showPage()
            y = height - 50
            c.setFont(hebrew_font, 10)

    y -= 20
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.827, 0.184, 0.184)
    c.line(50, y, width - 50, y)

    y -= 30
    c.setFont(hebrew_font, 12)
    subtotal = items_df['סהכ'].sum()
    contractor_discount = float(customer_data.get('contractor_discount', 0))
    sub_after = subtotal - contractor_discount
    vat = sub_after * 0.17
    discount_amount = (sub_after + vat) * (customer_data['discount'] / 100)
    total = sub_after + vat - discount_amount

    summary = [(rtl("סכום ביניים"), f"₪{subtotal:,.2f}")]
    if contractor_discount:
        summary.append((rtl("הנחת קבלן"), f"-₪{contractor_discount:,.2f}"))
    summary.extend([
        (rtl('מע"מ (17%)'), f"₪{vat:,.2f}"),
        (rtl(f"הנחה ({customer_data['discount']}%)"), f"-₪{discount_amount:,.2f}")
    ])
    for label, value in summary:
        c.drawRightString(200, y, label)
        c.drawRightString(70, y, value)
        y -= 25

    y -= 10
    c.setFont(hebrew_font, 14)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.drawRightString(200, y, rtl("סך הכל לתשלום"))
    c.drawRightString(70, y, f"₪{total:,.2f}")

    y -= 40
    c.setFont(hebrew_font, 9)
    conditions = [
        rtl("הצעת המחיר תקפה ל-14 ימים ממועד הפקתה."),
        rtl("ההצעה מיועדת ללקוח הספציפי בלבד ולא להעברה לחוץ."),
        rtl("המחירים עשויים להשתנות והחברה אינה אחראית לטעויות."),
        rtl("אישור ההצעה מהווה התחייבות לתשלום 10% מקדמה."),
        rtl("הלקוח מתחייב לפנות נקודות מים וחשמל בהתאם לתכניות."),
        rtl("אי עמידה בתנאים עלולה לגרור עיכובים וחריגות.")
    ]
    for line in conditions:
        c.drawRightString(width - 50, y, line)
        y -= 12
    y -= 20
    c.drawRightString(width - 50, y, rtl("חתימת הלקוח: _______________________"))

    c.showPage()

    for demo in [demo1, demo2]:
        if demo:
            img = ImageReader(demo)
            c.setFont(hebrew_font, 24)
            c.setFillColorRGB(0.827, 0.184, 0.184)
            c.drawCentredString(width / 2, height - 50, rtl("הדמיה"))
            w, h = img.getSize()
            max_w = width - 40 * mm
            max_h = height - 40 * mm
            ratio = min(max_w / w, max_h / h)
            nw = w * ratio
            nh = h * ratio
            x = (width - nw) / 2
            y_img = (height - nh) / 2
            c.drawImage(img, x, y_img, width=nw, height=nh)
            c.showPage()

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
            help="התמונה תתווסף כעמוד נפרד ב-PDF"
        )

        if demo_file:
            st.session_state.demo1 = demo_file
            st.success("ההדמיה נוספה בהצלחה!")
            # הצגת תצוגה מקדימה
            st.image(demo_file, caption="תצוגה מקדימה של ההדמיה", use_column_width=True)

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