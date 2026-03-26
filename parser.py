from __future__ import annotations

from docx import Document
import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    pages = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")

    return "\n".join(part.strip() for part in pages if part.strip())


def extract_text_from_docx(file_path: str) -> str:
    document = Document(file_path)
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(paragraphs)
