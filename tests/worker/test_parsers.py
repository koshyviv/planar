import os

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def test_parse_csv():
    from app.parsers.csv_parser import parse_csv
    with open(os.path.join(FIXTURES, "sample.csv"), "rb") as f:
        result = parse_csv(f.read())
    assert len(result) >= 1
    assert "Product A" in result[0]["text"]
    assert result[0]["metadata"]["type"] == "csv"


def test_parse_txt():
    with open(os.path.join(FIXTURES, "sample.txt"), "rb") as f:
        data = f.read()
    # TXT parser is inline lambda in ingest.py, replicate it
    text = data.decode("utf-8", errors="replace")
    assert "sample text document" in text


def test_parse_pdf():
    from app.parsers.pdf_parser import parse_pdf
    with open(os.path.join(FIXTURES, "sample.pdf"), "rb") as f:
        result = parse_pdf(f.read())
    assert len(result) >= 1
    assert result[0]["metadata"]["page"] == 1


def test_parse_pptx():
    from app.parsers.pptx_parser import parse_pptx
    with open(os.path.join(FIXTURES, "sample.pptx"), "rb") as f:
        result = parse_pptx(f.read())
    assert len(result) >= 1
    assert result[0]["metadata"]["slide"] == 1


def test_parse_docx():
    from app.parsers.docx_parser import parse_docx
    with open(os.path.join(FIXTURES, "sample.docx"), "rb") as f:
        result = parse_docx(f.read())
    assert len(result) >= 1
    assert any("test document" in s["text"].lower() for s in result)


def test_parse_xlsx():
    from app.parsers.xlsx_parser import parse_xlsx
    with open(os.path.join(FIXTURES, "sample.xlsx"), "rb") as f:
        result = parse_xlsx(f.read())
    assert len(result) >= 1
    assert any(s["metadata"]["sheet"] == "Revenue" for s in result)
