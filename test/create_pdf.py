from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

c = canvas.Canvas("cover.pdf", pagesize=A4)

width, height = A4

c.setFont("Helvetica", 14)
c.drawString(100, height - 100, "Sample PDF Document")

c.setFont("Helvetica", 10)
c.drawString(100, height - 140, "This is a harmless PDF used for steganography practice.")
c.drawString(100, height - 160, "Nothing suspicious here :)")

c.showPage()
c.save()
