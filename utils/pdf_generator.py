from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image

import os

def generate_pdf_and_jpg(user_data, output_dir="generated_files"):
    """
    Generate PDF and JPG for the user data.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf_path = os.path.join(output_dir, f"{user_data['name']}.pdf")
    jpg_path = os.path.join(output_dir, f"{user_data['name']}.jpg")

    # Create PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    c.drawString(100, 750, f"Name: {user_data['name']}")
    c.drawString(100, 730, f"Contact: {user_data['contact']}")
    c.drawString(100, 710, f"Email: {user_data['email']}")
    c.showPage()
    c.save()

    # Convert PDF to JPG
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, 300)
        pages[0].save(jpg_path, "JPEG")
    except Exception as e:
        print("PDF to JPG conversion failed:", e)

    return pdf_path, jpg_path
