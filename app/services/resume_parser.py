import os
import fitz
import pytesseract

tesseract_path = os.environ.get("TESSERACT_CMD")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

from PIL import Image
from io import BytesIO

from docx import Document


def extract_text_from_pdf(filepath):
    """
    Extract text from a PDF.
    If the PDF contains little/no text,
    use OCR instead.
    """

    text = ""

    document = fitz.open(filepath)

    for page in document:
        text += page.get_text()

    document.close()

    # If enough text was extracted, return it
    if len(text.strip()) >= 50:
        return text

    # Otherwise use OCR
    return extract_text_with_ocr(filepath)

def extract_text_with_ocr(filepath):
    """
    Extract text from scanned PDF using Tesseract OCR.
    """

    text = ""

    document = fitz.open(filepath)

    for page in document:

        pixmap = page.get_pixmap()

        image_bytes = pixmap.tobytes("png")

        image = Image.open(
            BytesIO(image_bytes)
        )

        page_text = pytesseract.image_to_string(image)

        text += page_text + "\n"

    document.close()

    return text


def extract_text_from_docx(filepath):
    """
    Extract text from a DOCX file.
    """

    document = Document(filepath)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_resume_text(filepath):
    """
    Determine the file type and extract its text.
    """

    if filepath.lower().endswith(".pdf"):
        return extract_text_from_pdf(filepath)

    elif filepath.lower().endswith(".docx"):
        return extract_text_from_docx(filepath)

    else:
        raise ValueError("Unsupported file type.")