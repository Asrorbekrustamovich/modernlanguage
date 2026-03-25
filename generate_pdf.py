from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Bu sinov uchun yaratilgan PDF hujjat.", ln=1, align="C")
pdf.cell(
    200, 10, txt="Eski qo'lyozma matni namunasi: 'Assalomu alaykum'.", ln=2, align="C"
)
pdf.output("test_document.pdf")
print("PDF created successfully.")
