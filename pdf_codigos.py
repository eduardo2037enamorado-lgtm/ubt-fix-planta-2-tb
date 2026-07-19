from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from barcodes import generate_qr_png, ubt_scan_url, ubt_to_barcode
from ubt_units import UBT_UNITS


def generate_codigos_pdf(base_url: str) -> bytes:
    buffer = BytesIO()
    page_width, page_height = letter
    margin = 0.45 * inch
    cols = 2
    rows = 4
    cell_width = (page_width - margin * 2) / cols
    cell_height = (page_height - margin * 2 - 0.5 * inch) / rows
    qr_size = min(cell_width - 0.35 * inch, cell_height - 1.0 * inch)

    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("UBT Fix Planta 2 TB - Codigos QR")

    for index, ubt in enumerate(UBT_UNITS):
        if index > 0 and index % (cols * rows) == 0:
            pdf.showPage()

        page_index = index % (cols * rows)
        col = page_index % cols
        row = page_index // cols

        x = margin + col * cell_width
        y = page_height - margin - 0.35 * inch - (row + 1) * cell_height

        if index % (cols * rows) == 0:
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(margin, page_height - margin, "UBT Fix Planta 2 TB - Etiquetas QR")
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin, page_height - margin - 14, f"Servidor: {base_url}")

        qr_bytes = generate_qr_png(ubt_scan_url(base_url, ubt))
        qr_image = ImageReader(BytesIO(qr_bytes))
        qr_x = x + (cell_width - qr_size) / 2
        qr_y = y + 0.55 * inch
        pdf.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size, preserveAspectRatio=True, mask="auto")

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(x + cell_width / 2, qr_y - 0.22 * inch, f"UBT {ubt}")

        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(x + cell_width / 2, qr_y - 0.42 * inch, ubt_to_barcode(ubt))

        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString(
            x + cell_width / 2,
            qr_y - 0.58 * inch,
            ubt_scan_url(base_url, ubt),
        )

        pdf.setStrokeColorRGB(0.82, 0.86, 0.9)
        pdf.rect(x + 0.08 * inch, y + 0.12 * inch, cell_width - 0.16 * inch, cell_height - 0.2 * inch)

    pdf.save()
    return buffer.getvalue()
