import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "worker"))

import pytest


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
