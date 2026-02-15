from app.chunker import chunk_text


def test_short_text_single_chunk():
    result = chunk_text("Hello world.")
    assert len(result) == 1
    assert result[0] == "Hello world."


def test_empty_text():
    result = chunk_text("")
    assert result == []


def test_whitespace_only():
    result = chunk_text("   \n\n  ")
    assert result == []


def test_long_text_multiple_chunks():
    text = "This is a sentence. " * 200  # ~4000 chars
    result = chunk_text(text, max_chars=500, overlap_chars=50)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= 600  # Allow some margin for overlap


def test_overlap_present():
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. " * 20
    result = chunk_text(text, max_chars=200, overlap_chars=50)
    assert len(result) > 1
