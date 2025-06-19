# file: panel_app/pdf_generator.py
import io
import os
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from PIL import Image as PILImage

from utils.helpers import asset_path
from utils.rtl import rtl


def create_enhanced_pdf(customer_data, items_df, demo1=None, demo2=None):
    """Create styled PDF"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    m = 20 * mm
    ROW_HEIGHT = 8 * mm  # הגדלת גובה השורות

    try:
        reg_path = asset_path('Heebo-Regular.ttf')
        bold_path = asset_path('Heebo-Bold.ttf')
        pdfmetrics.registerFont(TTFont('Heebo', reg_path))
        pdfmetrics.registerFont(TTFont('Heebo-Bold', bold_path))
        PDF_FONT = 'Heebo'
        PDF_BOLD = 'Heebo-Bold'
    except Exception:
        fallback = asset_path('Heebo-Regular.ttf')
        if os.path.exists(fallback):
            pdfmetrics.registerFont(TTFont('Hebrew', fallback))
            PDF_FONT = PDF_BOLD = 'Hebrew'
        else:
            PDF_FONT = PDF_BOLD = 'Helvetica'

    def draw_rtl(canv, x, y, text, font=PDF_FONT, fontsize=12):
        canv.setFont(font, fontsize)
        canv.drawRightString(x, y, rtl(text))

    def draw_watermark(canv):
        wm_path = asset_path('watermark.png')
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
        # פס אדום בתחתית
        canv.setFillColorRGB(0.827, 0.184, 0.184)
        canv.rect(0, 0, W, 3 * mm, fill=1, stroke=0)

        # לוגו קטן משמאל - משתמש באותו קובץ לוגו
        x = m
        logo_path = asset_path('logo.png')  # שימוש באותו קובץ לוגו
        if os.path.exists(logo_path):
            img = ImageReader(logo_path)
            w, h = img.getSize()
            scale = (8 * mm) / h  # הגדלת הלוגו בפוטר
            canv.drawImage(img, x, 4 * mm, height=8 * mm, width=w * scale, preserveAspectRatio=True, mask='auto')
            x += w * scale + 5 * mm

        # פרטי חברה משמאל לצד הלוגו
        canv.setFont(PDF_FONT, 9)  # הגדלת פונט
        canv.setFillColorRGB(0, 0, 0)
        info = "הנגרים 1 (מתחם הורדוס), באר שבע | טל: 072-393-3997 | דוא\"ל: info@panel-k.co.il"
        c.drawString(x, 7 * mm, rtl(info))

        # מספור עמודים מימין
        page_text = rtl(f"עמוד {page} מתוך {total}")
        canv.setFont(PDF_FONT, 9)
        canv.drawRightString(W - m, 7 * mm, page_text)

    def draw_header(canv):
        # מסגרת מעוצבת לכל העמוד
        canv.setStrokeColorRGB(0.827, 0.184, 0.184)
        canv.setLineWidth(2)
        canv.rect(m / 2, m / 2, W - m, H - m, fill=0, stroke=1)

        logo_big = asset_path('logo.png')
        logo_w = 70 * mm  # הגדלת הלוגו ל-70mm
        logo_h = 0
        if os.path.exists(logo_big):
            img = ImageReader(logo_big)
            w_img, h_img = img.getSize()
            ratio = logo_w / w_img
            logo_h = h_img * ratio
            # הלוגו קרוב יותר לפינה
            canv.drawImage(img, m / 2 + 5 * mm, H - m / 2 - logo_h - 5 * mm, width=logo_w, height=logo_h,
                           preserveAspectRatio=True, mask='auto')
        canv.setFont(PDF_BOLD, 42)  # הגדלת כותרת
        canv.setFillColorRGB(0.827, 0.184, 0.184)
        canv.drawCentredString(W / 2, H - m - logo_h - 15 * mm, rtl('הצעת מחיר'))
        return H - m - logo_h - 25 * mm

    pages_total = 1
    if demo1 or demo2:
        # כל תמונה בעמוד נפרד + עמוד לטקסט משפטי
        pages_total += (1 if demo1 else 0) + (1 if demo2 else 0) + 1

    page_num = 1

    y = draw_header(c)
    draw_watermark(c)
    c.setFillColorRGB(0, 0, 0)

    customer_details = [
        ("📱 לכבוד:", customer_data['name']),
        ("📅 תאריך:", customer_data['date'].strftime('%d/%m/%Y')),
        ("☎️ טלפון:", customer_data['phone']),
        ("✉️ דוא\"ל:", customer_data['email']),
        ("📍 כתובת:", customer_data['address']),
    ]
    for label, value in customer_details:
        draw_rtl(c, W - m, y, f"{label} {value}", font=PDF_FONT, fontsize=14)  # הגדלת פונט
        y -= 7 * mm
    y -= 8 * mm

    # כותרות טבלה - מחדש עם מרווחים טובים יותר
    c.setFont(PDF_BOLD, 12)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1, stroke=0)

    # הגדרת עמודות עם מרווחים נכונים
    col_widths = {
        'total': 40 * mm,
        'price': 40 * mm,
        'qty': 25 * mm,  # הקטנת עמודת כמות
        'product': W - 2 * m - 105 * mm  # עמודת מוצר גדולה יותר
    }

    # מיקומי עמודות - מימין לשמאל עם רווחים ברורים
    x_product = W - m - 5 * mm  # padding מימין
    x_qty = m + col_widths['total'] + col_widths['price'] + col_widths['qty'] - 3 * mm
    x_price = m + col_widths['total'] + col_widths['price'] - 3 * mm
    x_total = m + col_widths['total'] - 3 * mm

    # ציור גבולות עמודות
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=0, stroke=1)

    # כותרות
    c.setFillColorRGB(1, 1, 1)
    text_y = y - ROW_HEIGHT / 2 - 2
    draw_rtl(c, x_product, text_y, "מוצר", PDF_BOLD, 12)
    draw_rtl(c, x_qty + col_widths['qty'] - 5 * mm, text_y, "כמות", PDF_BOLD, 12)
    draw_rtl(c, x_price + col_widths['price'] - 5 * mm, text_y, "מחיר ליחידה", PDF_BOLD, 12)
    draw_rtl(c, x_total + col_widths['total'] - 5 * mm, text_y, "סה\"כ", PDF_BOLD, 12)

    y -= ROW_HEIGHT
    c.setFont(PDF_FONT, 11)  # הגדלת פונט בטבלה
    c.setFillColorRGB(0, 0, 0)

    for i, rec in enumerate(items_df.to_dict(orient='records')):
        # רקע לשורות זוגיות
        if i % 2 == 0:
            c.setFillColorRGB(0.9, 0.9, 0.9)  # צבע כהה יותר
            c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1, stroke=0)

        # גבולות שורה
        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=0, stroke=1)

        # טקסט
        c.setFillColorRGB(0, 0, 0)
        text_y = y - ROW_HEIGHT / 2 - 2

        # מוצר - עם padding וחיתוך אם ארוך מדי
        product_text = rec['הפריט']
        c.saveState()
        c.setFont(PDF_FONT, 11)
        # הגבלת רוחב הטקסט של המוצר
        max_width = col_widths['product'] - 10 * mm
        text_width = c.stringWidth(rtl(product_text), PDF_FONT, 11)
        if text_width > max_width:
            # חיתוך טקסט ארוך מדי
            while text_width > max_width and len(product_text) > 3:
                product_text = product_text[:-1]
                text_width = c.stringWidth(rtl(product_text + "..."), PDF_FONT, 11)
            product_text += "..."
        draw_rtl(c, x_product, text_y, product_text, PDF_FONT, 11)
        c.restoreState()

        # כמות - ממורכז בעמודה
        qty_text = str(int(rec['כמות']))
        c.drawCentredString(x_qty + col_widths['qty'] / 2, text_y, qty_text)

        # מחיר - יישור לימין עם padding
        price_text = f"₪{rec['מחיר יחידה']:,.2f}"
        c.drawRightString(x_price + col_widths['price'] - 5 * mm, text_y, price_text)

        # סה"כ - יישור לימין עם padding
        total_text = f"₪{rec['סהכ']:,.2f}"
        c.drawRightString(x_total + col_widths['total'] - 5 * mm, text_y, total_text)

        y -= ROW_HEIGHT

    y -= 15 * mm
    c.setLineWidth(3)  # קו עבה יותר
    c.setStrokeColorRGB(0.827, 0.184, 0.184)
    c.line(m, y, W - m, y)

    y -= 12 * mm
    c.setFont(PDF_FONT, 14)  # הגדלת פונט לסיכום
    subtotal = items_df['סהכ'].sum()
    contractor_discount = float(customer_data.get('contractor_discount', 0))
    sub_after = subtotal - contractor_discount
    vat = sub_after * 0.17
    discount_amount = (sub_after + vat) * (customer_data['discount'] / 100)
    total = sub_after + vat - discount_amount

    # תיבת סיכום עם רקע
    summary_box_height = 35 * mm
    c.setFillColorRGB(0.97, 0.97, 0.97)
    c.rect(W - m - 80 * mm, y - summary_box_height, 80 * mm, summary_box_height, fill=1, stroke=1)

    summary_lines = []
    if contractor_discount:
        summary_lines.append((rtl("הנחת קבלן"), f"-₪{contractor_discount:,.2f}"))
    summary_lines.extend([
        (rtl("סכום ביניים"), f"₪{sub_after:,.2f}"),
        (rtl('מע"מ (17%)'), f"₪{vat:,.2f}"),
        (rtl(f"הנחה ({customer_data['discount']}%)"), f"-₪{discount_amount:,.2f}")
    ])

    y_summary = y - 5 * mm
    for label, value in summary_lines:
        c.setFillColorRGB(0, 0, 0)
        c.drawRightString(W - m - 5 * mm, y_summary, label)
        c.drawRightString(W - m - 45 * mm, y_summary, value)
        y_summary -= 7 * mm

    # סך הכל בולט
    c.setLineWidth(2)
    c.setStrokeColorRGB(0.827, 0.184, 0.184)
    c.line(W - m - 75 * mm, y_summary - 2 * mm, W - m - 5 * mm, y_summary - 2 * mm)

    y_summary -= 7 * mm
    c.setFont(PDF_BOLD, 16)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    draw_rtl(c, W - m - 5 * mm, y_summary, "סך הכל לתשלום", PDF_BOLD, 16)
    c.drawRightString(W - m - 45 * mm, y_summary, f"₪{total:,.2f}")
    c.setFillColorRGB(0, 0, 0)

    if demo1 or demo2:
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1

        y_img = draw_header(c)
        draw_watermark(c)

        # חישוב גבהים לתמונות
        img_area_height = H - 80 * mm  # הרבה יותר מקום לתמונות

        if demo1:
            # תמונה ראשונה בעמוד נפרד
            c.setFont(PDF_FONT, 20)
            c.drawCentredString(W / 2, y_img, rtl("הדמיה"))
            y_img -= 10 * mm

            img1 = ImageReader(demo1)
            w1, h1 = img1.getSize()

            # גודל מקסימלי עם שוליים מינימליים
            max_w = W - 20 * mm  # שוליים של 10mm מכל צד
            max_h = img_area_height
            r1 = min(max_w / w1, max_h / h1)
            nw1, nh1 = w1 * r1, h1 * r1
            x1 = (W - nw1) / 2
            y1 = y_img - nh1

            # אם התמונה קטנה מדי, ממרכזים אותה אנכית
            if nh1 < max_h * 0.8:
                y1 = (y_img - (max_h - nh1) / 2) - nh1

            c.drawImage(img1, x1, y1, width=nw1, height=nh1)

            # עמוד חדש אם יש תמונה שנייה
            if demo2:
                draw_footer(c, page_num, pages_total)
                c.showPage()
                page_num += 1

                y_img = draw_header(c)
                draw_watermark(c)

        if demo2:
            # תמונה שנייה בעמוד נפרד
            c.setFont(PDF_FONT, 20)
            c.drawCentredString(W / 2, y_img, rtl("הדמיית נקודות מים וחשמל"))
            y_img -= 10 * mm

            img2 = ImageReader(demo2)
            w2, h2 = img2.getSize()

            # גודל מקסימלי עם שוליים מינימליים
            max_w = W - 20 * mm
            max_h = img_area_height
            r2 = min(max_w / w2, max_h / h2)
            nw2, nh2 = w2 * r2, h2 * r2
            x2 = (W - nw2) / 2
            y2 = y_img - nh2

            # אם התמונה קטנה מדי, ממרכזים אותה אנכית
            if nh2 < max_h * 0.8:
                y2 = (y_img - (max_h - nh2) / 2) - nh2

            c.drawImage(img2, x2, y2, width=nw2, height=nh2)

        # עמוד חדש לטקסט המשפטי תמיד
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1

        y = draw_header(c)
        draw_watermark(c)
        y -= 40 * mm  # מרווח גדול יותר מלמעלה

        # טקסט משפטי - בצבע שחור
        c.setFont(PDF_FONT, 10)  # הגדלת הפונט
        c.setFillColorRGB(0, 0, 0)  # צבע שחור
        for t in [
            "הצעת המחיר תקפה ל-14 ימים ממועד הפקתה.",
            "ההצעה מיועדת ללקוח הספציפי בלבד ולא להעברה לחוץ.",
            "המחירים עשויים להשתנות והחברה אינה אחראית לטעויות.",
            "אישור ההצעה מהווה התחייבות לתשלום 10% מקדמה.",
            "הלקוח מתחייב לפנות נקודות מים וחשמל בהתאם לתכניות.",
            "אי עמידה בתנאים עלולה לגרור עיכובים וחריגות."
        ]:
            draw_rtl(c, W - m, y, t, PDF_FONT, 10)
            y -= 5 * mm
        y -= 10 * mm

        c.setFillColorRGB(0, 0, 0)
        draw_rtl(c, W - m, y, "חתימת הלקוח: __________", PDF_FONT, 14)
        draw_footer(c, page_num, pages_total)
        c.showPage()
    else:
        y -= 10 * mm
        c.setFont(PDF_FONT, 10)  # הגדלת הפונט
        c.setFillColorRGB(0, 0, 0)  # צבע שחור
        for t in [
            "הצעת המחיר תקפה ל-14 ימים ממועד הפקתה.",
            "ההצעה מיועדת ללקוח הספציפי בלבד ולא להעברה לחוץ.",
            "המחירים עשויים להשתנות והחברה אינה אחראית לטעויות.",
            "אישור ההצעה מהווה התחייבות לתשלום 10% מקדמה.",
            "הלקוח מתחייב לפנות נקודות מים וחשמל בהתאם לתכניות.",
            "אי עמידה בתנאים עלולה לגרור עיכובים וחריגות."
        ]:
            draw_rtl(c, W - m, y, t, PDF_FONT, 10)
            y -= 5 * mm
        y -= 10 * mm
        if y < 40 * mm:
            y = 40 * mm
        c.setFillColorRGB(0, 0, 0)
        draw_rtl(c, W - m, y, "חתימת הלקוח: __________", PDF_FONT, 14)
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1

    c.save()
    buffer.seek(0)
    return buffer