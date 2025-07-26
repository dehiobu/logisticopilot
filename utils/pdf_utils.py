from fpdf import FPDF
from datetime import datetime

def generate_pdf(summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Logistics Manifest Summary - {datetime.now().strftime('%Y-%m-%d')}")
    pdf.ln()
    pdf.multi_cell(0, 10, summary_text)
    filename = f"/tmp/manifest_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename