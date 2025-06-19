# file: panel_app/catalog_loader.py
import pandas as pd
import streamlit as st


@st.cache_data
def load_catalog(file):
    try:
        df = pd.read_excel(file, sheet_name='גיליון1', header=8, engine='openpyxl')
        df.columns = df.columns.str.strip()

        rename_dict = {
            "מס'": "מספר",
            'סה"כ': 'סהכ'
        }
        df.rename(columns=rename_dict, inplace=True)

        for col in df.columns:
            if 'פריט' in col and col != 'הפריט':
                df.rename(columns={col: 'הפריט'}, inplace=True)
                break

        df['כמות'] = 0
        df['קטגוריה'] = ''
        current_category = ''

        for idx in df.index:
            if pd.isna(df.at[idx, 'מחיר יחידה']) or df.at[idx, 'מחיר יחידה'] == '':
                for col in df.columns:
                    if pd.notna(df.at[idx, col]) and str(df.at[idx, col]).strip() != '':
                        current_category = str(df.at[idx, col]).strip()
                        break
            else:
                df.at[idx, 'קטגוריה'] = current_category

        df = df[pd.notna(df['מחיר יחידה'])].copy()

        df['מחיר יחידה'] = pd.to_numeric(df['מחיר יחידה'], errors='coerce').fillna(0)

        if 'הערות' not in df.columns:
            df['הערות'] = ''
        df['הערות'] = df['הערות'].fillna('')

        return df
    except Exception as e:
        st.error(f"שגיאה בטעינת הקובץ: {str(e)}")
        return None
