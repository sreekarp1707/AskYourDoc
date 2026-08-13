import pdfplumber
from docx import Document


def extract_text(file):
    file_name = file.name.lower()

    if file_name.endswith(".pdf"):
        return extract_pdf_text(file)

    if file_name.endswith(".docx"):
        return extract_docx_text(file)

    if file_name.endswith(".txt"):
        return extract_txt_text(file)

    raise ValueError("Unsupported file format.")


def extract_pdf_text(file):
    text = ""

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


def extract_pdf_pages(file):
    pages = []

    with pdfplumber.open(file) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()

            if page_text:
                pages.append(
                    {
                        "page_number": page_number,
                        "text": page_text,
                    }
                )

    return pages


def extract_docx_text(file):
    document = Document(file)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )


def extract_txt_text(file):
    return file.read().decode("utf-8")