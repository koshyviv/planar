import io

from docx import Document


def parse_docx(data: bytes) -> list[dict]:
    """Parse DOCX and return list of {text, metadata}."""
    doc = Document(io.BytesIO(data))
    paragraphs = []
    current_section = []
    section_idx = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            if current_section:
                paragraphs.append({
                    "text": "\n".join(current_section),
                    "metadata": {"section": section_idx + 1},
                })
                current_section = []
                section_idx += 1
            continue
        current_section.append(text)

    if current_section:
        paragraphs.append({
            "text": "\n".join(current_section),
            "metadata": {"section": section_idx + 1},
        })

    return paragraphs if paragraphs else [{"text": "", "metadata": {}}]
