#!/usr/bin/env python3
"""
Generate test output with printers on floor diagram
"""

import json
import os
from floor_generator import generate_floor_svg, svg_to_png

OUTPUT_WIDTH = 2400
TEST_SPEC = os.path.join(os.path.dirname(__file__), "specs", "floor_template_5.json")
OUTPUT_SVG = os.path.join(os.path.dirname(__file__), "output", "test.svg")
OUTPUT_PNG = os.path.join(os.path.dirname(__file__), "output", "test.png")

def generate_test_diagram():
    """Generate test diagram with printers from spec"""
    
    # Load spec
    with open(TEST_SPEC, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    # Generate SVG WITH printers for test output
    svg_content = generate_floor_svg(spec, OUTPUT_WIDTH, include_printers=True)
    
    # Save SVG
    os.makedirs(os.path.dirname(OUTPUT_SVG), exist_ok=True)
    with open(OUTPUT_SVG, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    print(f"Generated SVG: {OUTPUT_SVG}")
    
    # Generate PNG
    if svg_to_png(svg_content, OUTPUT_PNG, OUTPUT_WIDTH, timeout=15):
        print(f"Generated PNG: {OUTPUT_PNG}")
    else:
        print("Failed to generate PNG")

if __name__ == "__main__":
    generate_test_diagram()

