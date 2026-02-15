#!/usr/bin/env python3
"""Generate a default PPTX template for Planar presentations.

Run once:  python3 assets/templates/create_template.py
"""
import os
from pptx import Presentation
from pptx.util import Inches

DIR = os.path.dirname(os.path.abspath(__file__))

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
prs.save(os.path.join(DIR, "default.pptx"))
print("Created default.pptx template")
