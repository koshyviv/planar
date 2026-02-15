from pypdf import PdfReader
import io


def parse_pdf(data: bytes) -> list[dict]:
    """Parse PDF and return list of {text, metadata} per page."""
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"text": text, "metadata": {"page": i + 1}})
    return pages
