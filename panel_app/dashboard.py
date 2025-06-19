# file: panel_app/dashboard.py
import os
from datetime import date

import pandas as pd
import streamlit as st

from catalog_loader import load_catalog
from pdf_generator import create_enhanced_pdf
from utils.helpers import asset_path
from utils.rtl import rtl


def render_dashboard():
    # Header with logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = asset_path('logo.png')
        if os.path.exists(logo_path):
            logo_col, title_col = st.columns([1, 3])
            with logo_col:
                st.image(logo_path, width=150)
            with title_col:
                st.markdown(
                    """
                    <div class="title-container">
                        <h1>מערכת הצעות מחיר</h1>
                        <p style="color: #666; margin: 0;">Panel Kitchens - מטבחים באיכות גבוהה</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div class="main-header">
                    <div class="title-container">
                        <h1>מערכת הצעות מחיר</h1>
                        <p style="color: #666; margin: 0;">Panel Kitchens - מטבחים באיכות גבוהה</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Session state initialization
    if 'customer_data' not in st.session_state:
        st.session_state.customer_data = {
            'name': '',
            'phone': '',
            'email': '',
            'address': '',
            'date': date.today(),
            'discount': 0.0,
            'contractor': False,
            'contractor_discount': 0.0,
        }

    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = pd.DataFrame()

    if 'demo1' not in st.session_state:
        st.session_state.demo1 = None
    if 'demo2' not in st.session_state:
        st.session_state.demo2 = None

    # UI Tabs
    tab1, tab2, tab3 = st.tabs(["📝 פרטי לקוח", "🛒 בחירת מוצרים", "📄 יצירת הצעה"])

    # Tab 1: customer details
    with tab1:
        st.subheader("הזן פרטי לקוח")

        col1, col2 = st.columns(2)
        with col1:
            st.session_state.customer_data['name'] = st.text_input(
                "שם הלקוח:",
                value=st.session_state.customer_data['name'],
                placeholder="הזן שם מלא",
            )
            st.session_state.customer_data['phone'] = st.text_input(
                "טלפון:",
                value=st.session_state.customer_data['phone'],
                placeholder="050-1234567",
            )
            st.session_state.customer_data['email'] = st.text_input(
                "דוא\"ל:",
                value=st.session_state.customer_data['email'],
                placeholder="name@example.com",
            )

        with col2:
            st.session_state.customer_data['date'] = st.date_input(
                "תאריך:",
                value=st.session_state.customer_data['date'],
            )
            st.session_state.customer_data['discount'] = st.number_input(
                "אחוז הנחה:",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.customer_data['discount'],
                step=5.0,
            )
            st.session_state.customer_data['contractor'] = st.checkbox(
                "הנחת קבלן",
                value=st.session_state.customer_data.get('contractor', False),
            )
            if st.session_state.customer_data['contractor']:
                st.session_state.customer_data['contractor_discount'] = st.number_input(
                    "סכום הנחת קבלן (₪):",
                    min_value=0.0,
                    value=st.session_state.customer_data.get('contractor_discount', 0.0),
                    step=100.0,
                    format="%.2f",
                )
            else:
                st.session_state.customer_data['contractor_discount'] = 0.0

        st.session_state.customer_data['address'] = st.text_area(
            "כתובת:",
            value=st.session_state.customer_data['address'],
            placeholder="רחוב, מספר, עיר",
            height=100,
        )

    # Tab 2: catalog selection
    with tab2:
        st.subheader("בחר מוצרים מהקטלוג")

        uploaded_file = st.file_uploader(
            "גרור קובץ קטלוג לכאן או לחץ לבחירה",
            type=['xlsx', 'xls'],
            help="קובץ Excel עם רשימת המוצרים",
        )

        if uploaded_file:
            catalog_df = load_catalog(uploaded_file)

            if catalog_df is not None:
                st.success("הקטלוג נטען בהצלחה!")

                st.markdown("### רשימת מוצרים - הזן כמות ליד כל מוצר")
                edited_df = catalog_df.copy()
                categories = edited_df['קטגוריה'].unique()

                for category in categories:
                    if category:
                        st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)

                    category_df = edited_df[edited_df['קטגוריה'] == category]

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
                                label_visibility="collapsed",
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

                selected_df = edited_df[edited_df['כמות'] > 0].copy()

                if not selected_df.empty:
                    st.session_state.selected_items = selected_df

                    st.markdown("### סיכום הזמנה")
                    display_columns = ['הפריט', 'הערות', 'כמות', 'מחיר יחידה', 'סהכ']
                    st.dataframe(
                        selected_df[display_columns],
                        use_container_width=True,
                        hide_index=True,
                    )

                    subtotal = selected_df['סהכ'].sum()
                    vat = subtotal * 0.17
                    discount = (subtotal + vat) * (st.session_state.customer_data['discount'] / 100)
                    total = subtotal + vat - discount

                    st.markdown(
                        f"""
                        <div class="summary-box">
                            <h4>סיכום תשלום:</h4>
                            <p>סכום ביניים: <b>₪{subtotal:,.2f}</b></p>
                            <p>מע"מ (17%): <b>₪{vat:,.2f}</b></p>
                            <p>הנחה ({st.session_state.customer_data['discount']}%): <b>-₪{discount:,.2f}</b></p>
                            <hr>
                            <h3>סך הכל לתשלום: <span style=\"color: #d32f2f;\">₪{total:,.2f}</span></h3>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("לא נבחרו מוצרים עדיין. הזן כמות ליד המוצרים הרצויים.")

    # Tab 3: create quote
    with tab3:
        st.subheader("יצירת הצעת מחיר")

        if not st.session_state.customer_data['name']:
            st.warning("יש להזין פרטי לקוח בטאב הראשון")
        elif isinstance(st.session_state.selected_items, pd.DataFrame) and st.session_state.selected_items.empty:
            st.warning("יש לבחור מוצרים בטאב השני")
        else:
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

            if st.button("🎯 צור הצעת מחיר", type="primary", use_container_width=True):
                with st.spinner("יוצר הצעת מחיר..."):
                    pdf_buffer = create_enhanced_pdf(
                        st.session_state.customer_data,
                        st.session_state.selected_items,
                        st.session_state.demo1,
                        st.session_state.demo2,
                    )

                    st.success("ההצעה נוצרה בהצלחה!")
                    st.download_button(
                        label="📥 הורד הצעת מחיר",
                        data=pdf_buffer,
                        file_name=f"הצעת_מחיר_{st.session_state.customer_data['name']}_{st.session_state.customer_data['email']}_{date.today()}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                    if st.button("🔄 התחל הצעה חדשה", use_container_width=True):
                        for key in st.session_state.keys():
                            del st.session_state[key]
                        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999;">
            <p>Panel Kitchens © 2025 | מערכת הצעות מחיר</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
