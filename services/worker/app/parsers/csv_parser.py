import csv
import io


def parse_csv(data: bytes) -> list[dict]:
    """Parse CSV and return as single text block with metadata."""
    text = data.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append(" | ".join(row))
    if rows:
        return [{"text": "\n".join(rows), "metadata": {"type": "csv"}}]
    return []
