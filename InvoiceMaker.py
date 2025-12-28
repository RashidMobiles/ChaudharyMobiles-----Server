from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import os


def generate_invoice(data):
    """
    Generates invoice PDF in-memory and returns a BytesIO stream
    Safe for FastAPI + MongoDB GridFS
    """

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ---------------- LOGO ----------------
    logo_path = os.path.join("assets", "RLogo.png")
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            40,
            height - 90,
            width=60,
            height=60,
            preserveAspectRatio=True,
            mask="auto"
        )

    # ---------------- HEADER ----------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(110, height - 50, "Chaudhary Mobile Shop")

    c.setFont("Helvetica", 9)
    c.drawString(110, height - 65, "Rashid Chaudhary")
    c.drawString(110, height - 80, "Near Allahbad Bank")
    c.drawString(110, height - 95, "Maudaha, Hamirpur 210507")
    c.drawString(110, height - 110, "+91 7268937279")

    c.setFont("Helvetica-Bold", 28)
    c.drawRightString(width - 40, height - 55, "INVOICE")

    # ---------------- INVOICE INFO ----------------
    y = height - 140

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Invoice to:")
    c.drawString(width - 200, y, "Invoice#")

    c.setFont("Helvetica", 10)
    c.drawString(40, y - 18, data["customer"]["name"])
    c.drawString(width - 200, y - 18, data.get("invoice_no", "N/A"))

    c.drawString(40, y - 35, data["customer"]["address"])
    c.drawString(width - 200, y - 35, "Date")
    c.drawString(width - 200, y - 52, data.get("date", ""))

    c.line(40, y - 75, width - 40, y - 75)

    # ---------------- TABLE HEADER ----------------
    table_y = y - 100
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, table_y, "Item")
    c.drawString(300, table_y, "Qty")
    c.drawString(380, table_y, "Unit Price")
    c.drawString(470, table_y, "Total")
    c.line(40, table_y - 8, width - 40, table_y - 8)

    # ---------------- TABLE ROWS ----------------
    row_y = table_y - 30
    subtotal = 0

    for item in data["items"]:
        qty = item.get("qty", 1)
        price = item.get("price", 0)
        total = qty * price
        subtotal += total

        # Main product row
        c.setFont("Helvetica", 10)
        c.drawString(40, row_y, item.get("name", "Item"))
        c.drawString(310, row_y, str(qty))
        c.drawString(390, row_y, f"{price}")
        c.drawString(470, row_y, f"{total}")

        row_y -= 15
        c.setFont("Helvetica", 9)

        category = item.get("category", "")

        # -------- PHONE LOGIC --------
        if category == "Phone":
            # IMEI(s)
            imeis = item.get("imei", [])
            for i, imei in enumerate(imeis[:2], start=1):
                c.drawString(60, row_y, f"IMEI {i}: {imei}")
                row_y -= 12

            # Charger Included
            if item.get("charger_included"):
                charger = item.get("charger")
                if charger:
                    c.drawString(60, row_y, "Charger Included:")
                    row_y -= 12
                    c.drawString(80, row_y, f"• {charger.get('name', '')}")
                    row_y -= 12
                    c.drawString(80, row_y, f"• Serial: {charger.get('serial', '')}")
                    row_y -= 12

        # -------- STANDALONE CHARGER --------
        elif category == "Charger":
            serial = item.get("serial")
            if serial:
                c.drawString(60, row_y, f"Serial No: {serial}")
                row_y -= 12

        row_y -= 10
        c.line(40, row_y + 5, width - 40, row_y + 5)

    # ---------------- PAYMENT METHOD ----------------
    pm_y = row_y - 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, pm_y, "PAYMENT METHOD")

    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        pm_y - 20,
        f"Mode: {data.get('payment', {}).get('mode', 'N/A')}"
    )

    # ---------------- TOTAL SUMMARY ----------------
    summary_y = pm_y
    c.setFont("Helvetica", 10)
    c.drawString(width - 200, summary_y, "Subtotal")
    c.drawRightString(width - 40, summary_y, f"{subtotal}")

    c.setFont("Helvetica-Bold", 16)
    c.drawString(width - 200, summary_y - 55, "Total")
    c.drawRightString(width - 40, summary_y - 55, f"{subtotal}")

    # ---------------- FOOTER ----------------
    c.setFont("Helvetica", 10)
    c.drawString(40, 120, "Thank you for your business!")

    c.line(width - 200, 130, width - 40, 130)
    c.drawString(width - 170, 110, "Authorized Signature")

    # Bottom strip
    c.setFillColor(colors.HexColor("#e0c36a"))
    c.rect(0, 0, width, 40, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.drawString(40, 15, "+91 7268937279")
    c.drawRightString(
        width - 40,
        15,
        "Near Allahbad Bank, Maudaha, Hamirpur 210507"
    )

    c.save()
    buffer.seek(0)
    return buffer
