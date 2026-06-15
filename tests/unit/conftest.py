import io

import pytest
from docx import Document as DocxDocument
from fpdf import FPDF


@pytest.fixture
def docx_bytes() -> bytes:
    doc = DocxDocument()
    doc.add_paragraph("Hello DOCX")
    doc.add_paragraph("Second paragraph")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.fixture
def pdf_bytes() -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Hello PDF")
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()
