import re


def chunk_text(text: str, max_chars: int = 2000, overlap_chars: int = 200) -> list[str]:
    """Split text into chunks, breaking at sentence boundaries when possible."""
    if not text.strip():
        return []

    if len(text) <= max_chars:
        return [text]

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if not sentence.strip():
            continue

        # If single sentence is too long, split by chars
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            for i in range(0, len(sentence), max_chars - overlap_chars):
                chunks.append(sentence[i:i + max_chars])
            continue

        if len(current_chunk) + len(sentence) + 1 > max_chars:
            chunks.append(current_chunk.strip())
            # Overlap: take the last portion of previous chunk
            if overlap_chars > 0 and current_chunk:
                overlap = current_chunk[-overlap_chars:]
                # Try to start at a word boundary
                space_idx = overlap.find(" ")
                if space_idx >= 0:
                    overlap = overlap[space_idx + 1:]
                current_chunk = overlap + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
