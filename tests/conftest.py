import pytest


@pytest.fixture
def sample_text():
    return "This is a sample document for testing the chunker. " * 50


@pytest.fixture
def sample_outline():
    return {
        "title": "Test Presentation",
        "slides": [
            {
                "title": "Introduction",
                "bullet_points": ["Point one", "Point two", "Point three"],
                "speaker_notes": "This is the introduction slide.",
            },
            {
                "title": "Main Content",
                "bullet_points": ["Detail A", "Detail B"],
                "speaker_notes": "Cover the main points here.",
            },
            {
                "title": "Conclusion",
                "bullet_points": ["Summary", "Next steps"],
                "speaker_notes": "Wrap up the presentation.",
            },
        ],
    }
