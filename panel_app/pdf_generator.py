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
    ROW_HEIGHT = 6 * mm

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

        # לוגו קטן משמאל
        x = m
        logo_small = asset_path('logo_small.png')
        if os.path.exists(logo_small):
            img = ImageReader(logo_small)
            w, h = img.getSize()
            scale = (5 * mm) / h
            canv.drawImage(img, x, 3 * mm, height=5 * mm, width=w * scale, preserveAspectRatio=True, mask='auto')
            x += w * scale + 5 * mm

        # פרטי חברה משמאל לצד הלוגו
        canv.setFont(PDF_FONT, 8)
        canv.setFillColorRGB(0, 0, 0)
        info = "הנגרים 1 (מתחם הורדוס), באר שבע | טל: 072-393-3997 | דוא\"ל: info@panel-k.co.il"
        c.drawString(x, 5 * mm, rtl(info))

        # מספור עמודים מימין
        page_text = rtl(f"עמוד {page} מתוך {total}")
        canv.setFont(PDF_FONT, 8)
        canv.drawRightString(W - m, 5 * mm, page_text)

    def draw_header(canv):
        logo_big = asset_path('logo.png')
        logo_w = 35 * mm
        logo_h = 0
        if os.path.exists(logo_big):
            img = ImageReader(logo_big)
            w_img, h_img = img.getSize()
            ratio = logo_w / w_img
            logo_h = h_img * ratio
            canv.drawImage(img, m, H - m - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        canv.setFont(PDF_BOLD, 36)
        canv.setFillColorRGB(0.827, 0.184, 0.184)
        canv.drawCentredString(W / 2, H - m - logo_h - 10 * mm, rtl('הצעת מחיר'))
        return H - m - logo_h - 20 * mm

    pages_total = 1 + int(demo1 is not None or demo2 is not None)
    page_num = 1

    y = draw_header(c)
    draw_watermark(c)
    c.setFillColorRGB(0, 0, 0)

    customer_details = [
        ("לכבוד:", customer_data['name']),
        ("תאריך:", customer_data['date'].strftime('%d/%m/%Y')),
        ("טלפון:", customer_data['phone']),
        ("דוא\"ל:", customer_data['email']),
        ("כתובת:", customer_data['address']),
    ]
    for label, value in customer_details:
        draw_rtl(c, W - m, y, f"{label} {value}", font=PDF_FONT, fontsize=12)
        y -= 6 * mm
    y -= 6 * mm

    c.setFont(PDF_FONT, 11)
    c.setFillColorRGB(0.827, 0.184, 0.184)
    c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1, stroke=0)
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    x_cols = [m, W - m - 120 * mm, W - m - 80 * mm, W - m - 40 * mm, W - m]
    for x_left, x_right in zip(x_cols, x_cols[1:]):
        c.rect(x_left, y - ROW_HEIGHT, x_right - x_left, ROW_HEIGHT, fill=0, stroke=1)
    c.setFillColorRGB(1, 1, 1)
    headers = [
        ("מוצר", W - m),
        ("כמות", W - m - 40 * mm),
        ("מחיר ליחידה", W - m - 80 * mm),
        ("סה\"כ", W - m - 120 * mm),
    ]
    text_y = y - ROW_HEIGHT / 2 + 2
    for text, pos in headers:
        draw_rtl(c, pos, text_y, text, PDF_FONT, fontsize=11)

    y -= ROW_HEIGHT
    c.setFont(PDF_FONT, 10)
    c.setFillColorRGB(0, 0, 0)
    x_cols = [m, W - m - 120 * mm, W - m - 80 * mm, W - m - 40 * mm, W - m]
    for i, rec in enumerate(items_df.to_dict(orient='records')):
        if i % 2 == 0:
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(m, y - ROW_HEIGHT, W - 2 * m, ROW_HEIGHT, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        text_y = y - ROW_HEIGHT / 2 - 1 * mm
        font_size = 10
        y_text = y - ROW_HEIGHT / 2 + font_size / 2
        draw_rtl(c, W - m, y_text, rec['הפריט'], PDF_FONT, font_size)
        c.drawRightString(W - m - 40 * mm, y_text, str(int(rec['כמות'])))
        c.drawRightString(W - m - 80 * mm, y_text, f"₪{rec['מחיר יחידה']:.2f}")
        c.drawRightString(W - m - 120 * mm, y_text, f"₪{rec['סהכ']:.2f}")

        c.setLineWidth(0.5)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        for x_left, x_right in zip(x_cols, x_cols[1:]):
            c.rect(x_left, y - ROW_HEIGHT, x_right - x_left, ROW_HEIGHT, fill=0, stroke=1)
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

    if demo1 or demo2:
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1

        y_img = draw_header(c)
        draw_watermark(c)
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
            y_img = y_img - nh2 - 20 * mm

        y = min(y_img, H - 30 * mm)
        c.setFont(PDF_FONT, 8)
        for t in [
            "הצעת המחיר תקפה ל-14 ימים ממועד הפקתה.",
            "ההצעה מיועדת ללקוח הספציפי בלבד ולא להעברה לחוץ.",
            "המחירים עשויים להשתנות והחברה אינה אחראית לטעויות.",
            "אישור ההצעה מהווה התחייבות לתשלום 10% מקדה.",
            "הלקוח מתחייב לפנות נקודות מים וחשמל בהתאם לתכניות.",
            "אי עמידה בתנאים עלולה לגרור עיכובים וחריגות."
        ]:
            draw_rtl(c, W - m, y, t, PDF_FONT, 8)
            y -= 4 * mm
        y -= 8 * mm
        if y < 30 * mm:
            y = 30 * mm
        draw_rtl(c, W - m, y, "חתימת הלקוח: ____________________", PDF_FONT, 12)
        c.setFont(PDF_FONT, 8)
        #company_info = "הנגרים 1 (מתחם הורדוס), באר שבע | טל: 072-393-3997 | דוא\"ל: info@panel-k.co.il"
        #c.drawString(m, 12 * mm, rtl(company_info))
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1
    else:
        y -= 10 * mm
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
        #c.drawString(m, 20 * mm, rtl("הנגרים 1 (מתחם הורדוס), באר שבע"))
        #c.drawString(m, 15 * mm, rtl("טל: 072-393-3997"))
        #c.drawString(m, 10 * mm, rtl("דוא\"ל: M@panel-k.co.il"))
        draw_footer(c, page_num, pages_total)
        c.showPage()
        page_num += 1

    c.save()
    buffer.seek(0)
    return buffer
