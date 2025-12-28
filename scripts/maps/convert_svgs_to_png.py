#!/usr/bin/env python3
"""
Convert all SVG files in output_test to PNG - optimized with browser reuse
"""

import os
import re
import tempfile
from pathlib import Path
from floor_generator import OUTPUT_WIDTH

def convert_all_svgs_fast(directory=None):
    """Convert all SVG files using a single browser instance for speed"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if directory:
        output_test_dir = directory
    else:
        output_test_dir = os.path.join(script_dir, "output_test")
    
    if not os.path.exists(output_test_dir):
        print(f"Directory {output_test_dir} does not exist!")
        return
    
    svg_files = [f for f in os.listdir(output_test_dir) if f.endswith('.svg')]
    
    if not svg_files:
        print("No SVG files found in output_test directory")
        return
    
    print(f"Found {len(svg_files)} SVG files to convert...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch browser ONCE and reuse for all conversions
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': OUTPUT_WIDTH, 'height': 2000},
                device_scale_factor=1
            )
            
            for svg_file in svg_files:
                svg_path = os.path.join(output_test_dir, svg_file)
                png_file = svg_file.replace('.svg', '.png')
                png_path = os.path.join(output_test_dir, png_file)
                
                # Skip if PNG already exists
                if os.path.exists(png_path):
                    print(f"  Skipping {svg_file} (PNG already exists)")
                    continue
                
                print(f"  Converting {svg_file} to {png_file}...")
                
                # Read SVG content
                with open(svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # Extract dimensions
                viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_content)
                if viewbox_match:
                    svg_width = int(viewbox_match.group(1))
                    svg_height = int(viewbox_match.group(2))
                    exact_height = int(OUTPUT_WIDTH * (svg_height / svg_width))
                else:
                    exact_height = int(OUTPUT_WIDTH * 0.583)
                
                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
                    tmp.write(svg_content)
                    tmp_path = tmp.name
                
                try:
                    page = context.new_page()
                    abs_path = os.path.abspath(tmp_path)
                    file_url = f'file:///{abs_path.replace(chr(92), "/")}'
                    
                    page.goto(file_url, wait_until='load', timeout=5000)
                    page.wait_for_timeout(50)  # Minimal wait
                    
                    svg_element = page.query_selector('svg')
                    if svg_element:
                        svg_element.screenshot(path=png_path)
                    else:
                        page.screenshot(path=png_path, full_page=True)
                    
                    page.close()
                    
                    if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
                        print(f"    ✓ Successfully created {png_file}")
                    else:
                        print(f"    ✗ Failed: PNG file not created or too small")
                except Exception as e:
                    print(f"    ✗ Failed: {e}")
                finally:
                    try:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    except:
                        pass
            
            browser.close()
            
    except ImportError:
        print("Playwright not installed. Falling back to individual conversions...")
        from floor_generator import svg_to_png
        for svg_file in svg_files:
            svg_path = os.path.join(output_test_dir, svg_file)
            png_file = svg_file.replace('.svg', '.png')
            png_path = os.path.join(output_test_dir, png_file)
            if os.path.exists(png_path):
                continue
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            svg_to_png(svg_content, png_path, OUTPUT_WIDTH, timeout=5)

def convert_all_svgs():
    """Wrapper for backward compatibility"""
    convert_all_svgs_fast()

if __name__ == "__main__":
    convert_all_svgs()

