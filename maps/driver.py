#!/usr/bin/env python3
"""
Floor Plan Generator - Grid-Based System
Uses 100px grid cells for perfect alignment
"""

import json
from xml.sax.saxutils import escape

INPUT_FILE = r"pmtm_database\maps\specs\test.json"
OUTPUT_SVG = r"pmtm_database\maps\output\test.svg"
OUTPUT_PNG = r"pmtm_database\maps\output\test.png"
OUTPUT_WIDTH = 2400

ROOM_COLORS = {
    'lab': '#FF9800',          # Orange - Computer Labs
    'classroom': '#2196F3',    # Blue - Classrooms/Lecture Halls
    'office': '#F44336',       # Red - Offices
    'library': '#9C27B0',      # Purple - Library
    'corridor': '#E0E0E0',     # Light Gray - Corridors/Halls
    'restroom': '#4CAF50',     # Green - Restrooms
    'stairs': '#9E9E9E',       # Gray - Stairs
    'elevator': '#607D8B',     # Blue Gray - Elevators
    'storage': '#757575',      # Dark Gray - Storage
    'lounge': '#00BCD4'        # Cyan - Lounges/Common Areas
}

def generate_floor_svg(spec, output_width):
    """Generate SVG from grid-based floor plan specification"""
    
    # Grid configuration
    GRID_SIZE = spec.get('grid_size', 100)
    GRID_COLS = spec.get('grid_cols', 24)
    GRID_ROWS = spec.get('grid_rows', 14)
    
    W = GRID_COLS * GRID_SIZE
    H = GRID_ROWS * GRID_SIZE
    out_h = int(output_width * (H / W))
    
    rooms = spec.get('rooms', [])
    doors = spec.get('doors', [])
    printers = spec.get('printers', [])
    entrance = spec.get('entrance')
    
    # Convert grid coordinates to pixel coordinates
    room_by_id = {}
    for r in rooms:
        room_data = {
            'id': r['id'],
            'x': r['grid_x'] * GRID_SIZE,
            'y': r['grid_y'] * GRID_SIZE,
            'w': r['grid_w'] * GRID_SIZE,
            'h': r['grid_h'] * GRID_SIZE,
            'label': r.get('label', ''),
            'type': r.get('type', 'corridor')
        }
        room_by_id[r['id']] = room_data
    
    def get_room_color(room_type):
        return ROOM_COLORS.get(room_type, '#FFFFFF')
    
    def get_text_color(room_type):
        """Get text color based on room type - dark for light backgrounds"""
        light_bg_types = {'corridor', 'lounge'}
        return '#1a1a1a' if room_type in light_bg_types else 'white'
    
    def should_rotate_text(label, w, h):
        """Only rotate if individual words don't fit horizontally"""
        if not label:
            return False
        # Check if any single word is too long for horizontal space
        words = label.split()
        max_word_len = max(len(word) for word in words) if words else 0
        # Rough estimate: each char needs ~20px, leave margins
        can_fit_horizontal = (max_word_len * 20) < (w - 40)
        return not can_fit_horizontal and h > w
    
    def printer_pos(p):
        """Calculate absolute printer position from grid"""
        room = room_by_id.get(p['room'])
        if not room:
            return {'x': 0, 'y': 0}
        
        rx = p.get('grid_rx', 0.5)
        ry = p.get('grid_ry', 0.5)
        
        x = room['x'] + (rx * room['w'])
        y = room['y'] + (ry * room['h'])
        
        return {'x': x, 'y': y}
    
    # ROOMS - Draw all rooms perfectly aligned to grid
    room_elems = []
    for room_id, r in room_by_id.items():
        if not r['label']:  # Skip rooms with no label (filler rooms)
            color = get_room_color(r['type'])
            room_elems.append(f'''<rect x="{r['x']}" y="{r['y']}" width="{r['w']}" height="{r['h']}" 
                  fill="{color}" stroke="none"/>''')
            continue
        
        color = get_room_color(r['type'])
        text_color = get_text_color(r['type'])
        rotate = should_rotate_text(r['label'], r['w'], r['h'])
        
        # Room rectangle
        room_elems.append(f'''<rect x="{r['x']}" y="{r['y']}" width="{r['w']}" height="{r['h']}" 
              fill="{color}" stroke="none"/>''')
        
        # Text label
        cx = r['x'] + r['w']/2
        cy = r['y'] + r['h']/2
        
        # Split text into multiple lines if needed (horizontal preferred)
        words = r['label'].split()
        
        if rotate:
            # Vertical text (rare case)
            label = f'''<text x="{cx}" y="{cy}" 
                  font-family="Roboto,Segoe UI,Arial,sans-serif" 
                  font-size="40" font-weight="600"
                  fill="{text_color}" text-anchor="middle" dominant-baseline="middle"
                  transform="rotate(-90 {cx} {cy})">
              {escape(r['label'])}
            </text>'''
        elif len(words) > 2:
            # Multi-line horizontal text
            line_height = 45
            num_lines = min(len(words), 3)  # Max 3 lines
            start_y = cy - ((num_lines - 1) * line_height / 2)
            
            label = '<g>'
            if len(words) == 3:
                lines = [[words[0]], [words[1]], [words[2]]]
            elif len(words) == 4:
                lines = [[words[0], words[1]], [words[2], words[3]]]
            else:
                # Split into roughly equal parts
                mid = len(words) // 2
                lines = [words[:mid], words[mid:]]
            
            for i, line in enumerate(lines):
                line_text = ' '.join(line)
                label += f'''<text x="{cx}" y="{start_y + i * line_height}" 
                      font-family="Roboto,Segoe UI,Arial,sans-serif" 
                      font-size="40" font-weight="600"
                      fill="{text_color}" text-anchor="middle" dominant-baseline="middle">
                  {escape(line_text)}
                </text>'''
            label += '</g>'
        else:
            # Single line horizontal text
            label = f'''<text x="{cx}" y="{cy}" 
                  font-family="Roboto,Segoe UI,Arial,sans-serif" 
                  font-size="40" font-weight="600"
                  fill="{text_color}" text-anchor="middle" dominant-baseline="middle">
              {escape(r['label'])}
            </text>'''
        
        room_elems.append(label)
    
    # DOORS - Convert grid to pixel coordinates
    door_elems = []
    for d in doors:
        dx = d['grid_x'] * GRID_SIZE
        dy = d['grid_y'] * GRID_SIZE
        
        if d.get('orientation') == 'horizontal':
            door_elems.append(f'''<rect x="{dx-25}" y="{dy-4}" width="50" height="8" 
                  fill="white" stroke="#666" stroke-width="2"/>''')
        else:
            door_elems.append(f'''<rect x="{dx-4}" y="{dy-25}" width="8" height="50" 
                  fill="white" stroke="#666" stroke-width="2"/>''')
    
    # PRINTERS
    printer_elems = []
    for p in printers:
        pos = printer_pos(p)
        label = p.get('label', p['id'])
        
        # Printer icon - 50x50px
        printer_elems.append(f'''
    <!-- Printer {escape(p['id'])} -->
    <rect x="{pos['x']-25}" y="{pos['y']-25}" width="50" height="50" 
          fill="#2C3E50" stroke="#FFF" stroke-width="3" rx="5"/>
    <rect x="{pos['x']-20}" y="{pos['y']-30}" width="40" height="8" 
          fill="#7F8C8D" rx="2"/>
    <rect x="{pos['x']-15}" y="{pos['y']-10}" width="30" height="18" 
          fill="white" rx="2"/>
    <line x1="{pos['x']-10}" y1="{pos['y']-5}" x2="{pos['x']+10}" y2="{pos['y']-5}" 
          stroke="#2C3E50" stroke-width="2"/>
    <line x1="{pos['x']-10}" y1="{pos['y']+2}" x2="{pos['x']+10}" y2="{pos['y']+2}" 
          stroke="#2C3E50" stroke-width="2"/>
    <text x="{pos['x']}" y="{pos['y']+45}" 
          font-family="Roboto,Segoe UI,Arial,sans-serif" 
          font-size="24" font-weight="700"
          fill="#1a1a1a" text-anchor="middle">
      {escape(label)}
    </text>''')
    
    # ENTRANCE marker - REMOVED per user request
    entrance_elem = ''
    
    # Building outline
    border = f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#222" stroke-width="8"/>'
    
    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     viewBox="0 0 {W} {H}" 
     width="{output_width}" 
     height="{out_h}"
     style="display:block; max-width:100%; height:auto;">
  <defs>
    <style>
      text {{ 
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }}
    </style>
  </defs>
  
  <!-- Background -->
  <rect x="0" y="0" width="{W}" height="{H}" fill="#f5f5f5"/>
  
  <!-- Grid lines (for debugging - remove in production) -->
  <!--
  {chr(10).join([f'<line x1="{i*GRID_SIZE}" y1="0" x2="{i*GRID_SIZE}" y2="{H}" stroke="#ddd" stroke-width="0.5"/>' for i in range(GRID_COLS+1)])}
  {chr(10).join([f'<line x1="0" y1="{i*GRID_SIZE}" x2="{W}" y2="{i*GRID_SIZE}" stroke="#ddd" stroke-width="0.5"/>' for i in range(GRID_ROWS+1)])}
  -->
  
  <!-- Rooms -->
  {chr(10).join(room_elems)}
  
  <!-- Doors -->
  {chr(10).join(door_elems)}
  
  <!-- Entrance -->
  {entrance_elem}
  
  <!-- Printers -->
  {chr(10).join(printer_elems)}
  
  <!-- Building outline -->
  {border}
</svg>'''
    
    return svg


def svg_to_png(svg_content, output_path, width):
    """Convert SVG to PNG"""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f'file:///{os.path.abspath(tmp_path).replace(chr(92), "/")}')
                page.set_viewport_size({"width": width, "height": int(width * 0.583)})
                page.screenshot(path=output_path, full_page=True)
                browser.close()
            return True
        finally:
            os.unlink(tmp_path)
    except:
        pass
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(f'file:///{os.path.abspath(tmp_path).replace(chr(92), "/")}')
            driver.save_screenshot(output_path)
            driver.quit()
            return True
        finally:
            os.unlink(tmp_path)
    except:
        pass
    
    return False


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    svg_content = generate_floor_svg(spec, output_width=OUTPUT_WIDTH)
    
    with open(OUTPUT_SVG, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"✓ SVG: {OUTPUT_SVG}")
    
    if svg_to_png(svg_content, OUTPUT_PNG, width=OUTPUT_WIDTH):
        print(f"✓ PNG: {OUTPUT_PNG}")
    else:
        print(f"✗ PNG skipped (install playwright or selenium)")
    
    print("\nDone!")


if __name__ == "__main__":
    main()