#!/usr/bin/env python3
"""
Floor Plan Generator - JSON spec to SVG/PNG
Reads from floor_spec.json, outputs to floor_plan.svg and floor_plan.png
Professional layout with colored rooms, no borders, wall-mounted printers
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

INPUT_FILE = r"pmtm_database\maps\specs\test.json"
OUTPUT_SVG = r"pmtm_database\maps\output\test.svg"
OUTPUT_PNG = r"pmtm_database\maps\output\test.png"
OUTPUT_WIDTH = 1200

# Professional color scheme for room types
ROOM_COLORS = {
    'lab': '#FFB84D',           # Orange - Computer Lab
    'classroom': '#4A90E2',     # Blue - Lecture Hall/Study Room
    'office': '#E74C3C',        # Red - Faculty Office/Meeting Room
    'library': '#9B59B6',       # Purple - Library
    'corridor': '#ECF0F1',      # Light Gray - Corridors/Halls
    'restroom': '#2ECC71',      # Green - Restrooms
    'stairs': '#95A5A6',        # Gray - Stairs
    'elevator': '#34495E',      # Dark Gray - Elevator
    'storage': '#7F8C8D'        # Medium Gray - Storage
}

def generate_floor_svg(spec, output_width):
    """Generate SVG from floor plan specification"""
    
    W = spec.get('width', 1000)
    H = spec.get('height', 600)
    out_h = int(output_width * (H / W))
    
    rooms = spec.get('rooms', [])
    doors = spec.get('doors', [])
    windows = spec.get('windows', [])
    stairs = spec.get('stairs', [])
    elevators = spec.get('elevators', [])
    printers = spec.get('printers', [])
    entrance = spec.get('entrance')
    
    # Build room lookup
    room_by_id = {r['id']: r for r in rooms}
    
    def get_room_color(room):
        """Get color for room based on type"""
        room_type = room.get('type', 'corridor')
        return ROOM_COLORS.get(room_type, '#FFFFFF')
    
    def get_text_rotation(room):
        """Determine if text should be vertical based on room dimensions"""
        w = room.get('w', 0)
        h = room.get('h', 0)
        # If height is significantly more than width, use vertical text
        return 'vertical' if h > w * 1.3 else 'horizontal'
    
    def printer_pos(p):
        """Calculate printer position near walls"""
        room = room_by_id.get(p['room'])
        if not room:
            return {'x': p.get('x', 0), 'y': p.get('y', 0)}
        
        # Place printer near walls based on relative position
        if 'rx' in p and 'ry' in p:
            rx, ry = p['rx'], p['ry']
            
            # Snap to nearest wall
            if rx < 0.3:  # Near left wall
                x = room['x'] + 25
            elif rx > 0.7:  # Near right wall
                x = room['x'] + room['w'] - 25
            else:  # Center horizontally
                x = room['x'] + (rx * room['w'])
            
            if ry < 0.3:  # Near top wall
                y = room['y'] + 25
            elif ry > 0.7:  # Near bottom wall
                y = room['y'] + room['h'] - 25
            else:  # Center vertically
                y = room['y'] + (ry * room['h'])
        else:
            x = p.get('x', room['x'] + room['w']/2)
            y = p.get('y', room['y'] + room['h']/2)
            
        return {'x': x, 'y': y}
    
    # Generate SVG elements
    room_elems = []
    for r in rooms:
        color = get_room_color(r)
        rotation = get_text_rotation(r)
        
        # Calculate text position and rotation
        cx = r['x'] + r['w']/2
        cy = r['y'] + r['h']/2
        
        if rotation == 'vertical':
            transform = f'rotate(-90 {cx} {cy})'
            text_anchor = 'middle'
        else:
            transform = ''
            text_anchor = 'middle'
        
        room_elems.append(f'''<g class="room" data-room="{escape(r['id'])}">
      <rect x="{r['x']}" y="{r['y']}" width="{r['w']}" height="{r['h']}" 
            fill="{color}" stroke="none"/>
      <text x="{cx}" y="{cy}" 
            font-family="Helvetica,Arial,sans-serif" font-size="16" font-weight="500"
            fill="#333" text-anchor="{text_anchor}" dominant-baseline="middle"
            transform="{transform}">
        {escape(r.get('label', r['id']))}
      </text>
    </g>''')
    
    # Add wall lines (thin lines between rooms)
    wall_elems = []
    for r in rooms:
        x1, y1 = r['x'], r['y']
        x2, y2 = r['x'] + r['w'], r['y'] + r['h']
        
        # Draw walls only where rooms meet
        wall_elems.append(f'''<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y1}" 
              stroke="#999" stroke-width="1.5" opacity="0.3"/>''')
        wall_elems.append(f'''<line x1="{x2}" y1="{y1}" x2="{x2}" y2="{y2}" 
              stroke="#999" stroke-width="1.5" opacity="0.3"/>''')
    
    # Draw doors
    door_elems = []
    for d in doors:
        if d.get('orientation') == 'horizontal':
            door_elems.append(f'''<rect x="{d['x']-15}" y="{d['y']-2}" width="30" height="4" 
              fill="white" stroke="#666" stroke-width="1.5"/>''')
        else:  # vertical
            door_elems.append(f'''<rect x="{d['x']-2}" y="{d['y']-15}" width="4" height="30" 
              fill="white" stroke="#666" stroke-width="1.5"/>''')
    
    # Draw windows
    window_elems = []
    for w in windows:
        if w.get('orientation') == 'horizontal':
            window_elems.append(f'''<rect x="{w['x']-20}" y="{w['y']-2}" width="40" height="4" 
              fill="#87CEEB" stroke="#4682B4" stroke-width="1"/>''')
        else:  # vertical
            window_elems.append(f'''<rect x="{w['x']-2}" y="{w['y']-20}" width="4" height="40" 
              fill="#87CEEB" stroke="#4682B4" stroke-width="1"/>''')
    
    # Draw stairs
    stairs_elems = []
    for s in stairs:
        if s.get('direction') == 'horizontal':
            stairs_elems.append(f'''<g class="stairs">
          <rect x="{s['x']}" y="{s['y']}" width="80" height="50" fill="#95A5A6" stroke="none"/>
          <text x="{s['x']+40}" y="{s['y']+30}" font-family="Helvetica,Arial,sans-serif" 
                font-size="12" fill="white" text-anchor="middle">
            {escape(s.get('label', 'Stairs'))}
          </text>
        </g>''')
        else:
            stairs_elems.append(f'''<g class="stairs">
          <rect x="{s['x']}" y="{s['y']}" width="50" height="80" fill="#95A5A6" stroke="none"/>
          <text x="{s['x']+25}" y="{s['y']+40}" font-family="Helvetica,Arial,sans-serif" 
                font-size="12" fill="white" text-anchor="middle">
            {escape(s.get('label', 'Stairs'))}
          </text>
        </g>''')
    
    # Draw elevators
    elevator_elems = []
    for e in elevators:
        elevator_elems.append(f'''<g class="elevator">
      <rect x="{e['x']}" y="{e['y']}" width="60" height="60" fill="#34495E" 
            stroke="none" rx="2"/>
      <text x="{e['x']+30}" y="{e['y']+35}" font-family="Helvetica,Arial,sans-serif" 
            font-size="12" fill="white" text-anchor="middle" font-weight="bold">
        LIFT
      </text>
    </g>''')
    
    # Draw printers with icon
    printer_elems = []
    for p in printers:
        pos = printer_pos(p)
        label = p.get('label', p['id'])
        
        # Printer icon (simplified)
        printer_elems.append(f'''<g class="printer" data-id="{escape(p['id'])}">
      <!-- Printer icon -->
      <rect x="{pos['x']-8}" y="{pos['y']-8}" width="16" height="16" 
            fill="#2C3E50" stroke="none" rx="2"/>
      <rect x="{pos['x']-6}" y="{pos['y']-10}" width="12" height="3" 
            fill="#95A5A6" stroke="none"/>
      <rect x="{pos['x']-4}" y="{pos['y']-3}" width="8" height="5" 
            fill="white" stroke="none"/>
      <!-- Label -->
      <text x="{pos['x']}" y="{pos['y']+18}" 
            font-family="Helvetica,Arial,sans-serif" font-size="11" font-weight="500"
            fill="#2C3E50" text-anchor="middle">
        {escape(label)}
      </text>
    </g>''')
    
    # Draw entrance marker
    entrance_elem = ''
    if entrance:
        entrance_elem = f'''<g class="entrance">
      <circle cx="{entrance['x']}" cy="{entrance['y']}" r="12" 
              fill="#E74C3C" stroke="white" stroke-width="2"/>
      <text x="{entrance['x']}" y="{entrance['y']-18}" 
            font-family="Helvetica,Arial,sans-serif" font-size="12" font-weight="bold"
            fill="#E74C3C" text-anchor="middle">
        {escape(entrance.get('label', 'ENTRANCE'))}
      </text>
    </g>'''
    
    # Outer border
    border_elem = f'''<rect x="0" y="0" width="{W}" height="{H}" 
          fill="none" stroke="#333" stroke-width="4"/>'''
    
    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" 
     width="{output_width}" height="{out_h}" preserveAspectRatio="xMidYMid meet">
  <defs>
    <style>
      text {{ 
        pointer-events: none;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }}
      .room:hover rect {{ opacity: 0.9; }}
    </style>
  </defs>
  
  {chr(10).join(room_elems)}
  {chr(10).join(wall_elems)}
  {chr(10).join(door_elems)}
  {chr(10).join(window_elems)}
  {chr(10).join(stairs_elems)}
  {chr(10).join(elevator_elems)}
  {entrance_elem}
  {chr(10).join(printer_elems)}
  {border_elem}
</svg>'''
    
    return svg


def svg_to_png(svg_content, output_path, width):
    """Convert SVG to PNG using Playwright (most reliable cross-platform)
    
    Install with: pip install playwright && playwright install chromium
    Or: pip install selenium (requires Chrome browser)
    """
    
    # Try Playwright (best option - pure Python, reliable)
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
                page.set_viewport_size({"width": width, "height": int(width * 0.6)})
                page.screenshot(path=output_path, full_page=True)
                browser.close()
            return True
        finally:
            os.unlink(tmp_path)
    except ImportError:
        pass
    except Exception as e:
        print(f"Playwright error: {e}")
    
    # Try Selenium + Chrome
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
    except Exception as e:
        pass
    
    print("\nPNG conversion requires browser automation. Install ONE of:")
    print("  pip install playwright && playwright install chromium  (recommended)")
    print("  pip install selenium  (requires Chrome browser installed)")
    print("\nOr just use the SVG file - it's vector and works perfectly in web/React.")
    return False


def main():
    # Load spec from input file
    with open(INPUT_FILE, 'r') as f:
        spec = json.load(f)
    
    # Generate SVG
    svg_content = generate_floor_svg(spec, output_width=OUTPUT_WIDTH)
    
    # Save SVG
    with open(OUTPUT_SVG, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"✓ Generated: {OUTPUT_SVG}")
    
    # Save PNG
    try:
        if svg_to_png(svg_content, OUTPUT_PNG, width=OUTPUT_WIDTH):
            print(f"✓ Generated: {OUTPUT_PNG}")
        else:
            print(f"✗ PNG generation skipped")
    except Exception as e:
        print(f"✗ PNG generation failed: {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Floor Plan Generator - JSON spec to SVG/PNG
Reads from floor_spec.json, outputs to floor_plan.svg and floor_plan.png
Professional layout with colored rooms, no borders, wall-mounted printers
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

INPUT_FILE = r"pmtm_database\maps\specs\test.json"
OUTPUT_SVG = r"pmtm_database\maps\output\test.svg"
OUTPUT_PNG = r"pmtm_database\maps\output\test.png"
OUTPUT_WIDTH = 1200

# Professional color scheme for room types
ROOM_COLORS = {
    'lab': '#FFB84D',           # Orange - Computer Lab
    'classroom': '#4A90E2',     # Blue - Lecture Hall/Study Room
    'office': '#E74C3C',        # Red - Faculty Office/Meeting Room
    'library': '#9B59B6',       # Purple - Library
    'corridor': '#ECF0F1',      # Light Gray - Corridors/Halls
    'restroom': '#2ECC71',      # Green - Restrooms
    'stairs': '#95A5A6',        # Gray - Stairs
    'elevator': '#34495E',      # Dark Gray - Elevator
    'storage': '#7F8C8D'        # Medium Gray - Storage
}

def generate_floor_svg(spec, output_width):
    """Generate SVG from floor plan specification"""
    
    W = spec.get('width', 1000)
    H = spec.get('height', 600)
    out_h = int(output_width * (H / W))
    
    rooms = spec.get('rooms', [])
    doors = spec.get('doors', [])
    windows = spec.get('windows', [])
    stairs = spec.get('stairs', [])
    elevators = spec.get('elevators', [])
    printers = spec.get('printers', [])
    entrance = spec.get('entrance')
    
    # Build room lookup
    room_by_id = {r['id']: r for r in rooms}
    
    def get_room_color(room):
        """Get color for room based on type"""
        room_type = room.get('type', 'corridor')
        return ROOM_COLORS.get(room_type, '#FFFFFF')
    
    def get_text_rotation(room):
        """Determine if text should be vertical based on room dimensions"""
        w = room.get('w', 0)
        h = room.get('h', 0)
        # If height is significantly more than width, use vertical text
        return 'vertical' if h > w * 1.3 else 'horizontal'
    
    def printer_pos(p):
        """Calculate printer position near walls"""
        room = room_by_id.get(p['room'])
        if not room:
            return {'x': p.get('x', 0), 'y': p.get('y', 0)}
        
        # Place printer near walls based on relative position
        if 'rx' in p and 'ry' in p:
            rx, ry = p['rx'], p['ry']
            
            # Snap to nearest wall
            if rx < 0.3:  # Near left wall
                x = room['x'] + 25
            elif rx > 0.7:  # Near right wall
                x = room['x'] + room['w'] - 25
            else:  # Center horizontally
                x = room['x'] + (rx * room['w'])
            
            if ry < 0.3:  # Near top wall
                y = room['y'] + 25
            elif ry > 0.7:  # Near bottom wall
                y = room['y'] + room['h'] - 25
            else:  # Center vertically
                y = room['y'] + (ry * room['h'])
        else:
            x = p.get('x', room['x'] + room['w']/2)
            y = p.get('y', room['y'] + room['h']/2)
            
        return {'x': x, 'y': y}
    
    # Generate SVG elements
    room_elems = []
    for r in rooms:
        color = get_room_color(r)
        rotation = get_text_rotation(r)
        
        # Calculate text position and rotation
        cx = r['x'] + r['w']/2
        cy = r['y'] + r['h']/2
        
        if rotation == 'vertical':
            transform = f'rotate(-90 {cx} {cy})'
            text_anchor = 'middle'
        else:
            transform = ''
            text_anchor = 'middle'
        
        room_elems.append(f'''<g class="room" data-room="{escape(r['id'])}">
      <rect x="{r['x']}" y="{r['y']}" width="{r['w']}" height="{r['h']}" 
            fill="{color}" stroke="none"/>
      <text x="{cx}" y="{cy}" 
            font-family="Helvetica,Arial,sans-serif" font-size="16" font-weight="500"
            fill="#333" text-anchor="{text_anchor}" dominant-baseline="middle"
            transform="{transform}">
        {escape(r.get('label', r['id']))}
      </text>
    </g>''')
    
    # Add wall lines (thin lines between rooms)
    wall_elems = []
    for r in rooms:
        x1, y1 = r['x'], r['y']
        x2, y2 = r['x'] + r['w'], r['y'] + r['h']
        
        # Draw walls only where rooms meet
        wall_elems.append(f'''<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y1}" 
              stroke="#999" stroke-width="1.5" opacity="0.3"/>''')
        wall_elems.append(f'''<line x1="{x2}" y1="{y1}" x2="{x2}" y2="{y2}" 
              stroke="#999" stroke-width="1.5" opacity="0.3"/>''')
    
    # Draw doors
    door_elems = []
    for d in doors:
        if d.get('orientation') == 'horizontal':
            door_elems.append(f'''<rect x="{d['x']-15}" y="{d['y']-2}" width="30" height="4" 
              fill="white" stroke="#666" stroke-width="1.5"/>''')
        else:  # vertical
            door_elems.append(f'''<rect x="{d['x']-2}" y="{d['y']-15}" width="4" height="30" 
              fill="white" stroke="#666" stroke-width="1.5"/>''')
    
    # Draw windows
    window_elems = []
    for w in windows:
        if w.get('orientation') == 'horizontal':
            window_elems.append(f'''<rect x="{w['x']-20}" y="{w['y']-2}" width="40" height="4" 
              fill="#87CEEB" stroke="#4682B4" stroke-width="1"/>''')
        else:  # vertical
            window_elems.append(f'''<rect x="{w['x']-2}" y="{w['y']-20}" width="4" height="40" 
              fill="#87CEEB" stroke="#4682B4" stroke-width="1"/>''')
    
    # Draw stairs
    stairs_elems = []
    for s in stairs:
        if s.get('direction') == 'horizontal':
            stairs_elems.append(f'''<g class="stairs">
          <rect x="{s['x']}" y="{s['y']}" width="80" height="50" fill="#95A5A6" stroke="none"/>
          <text x="{s['x']+40}" y="{s['y']+30}" font-family="Helvetica,Arial,sans-serif" 
                font-size="12" fill="white" text-anchor="middle">
            {escape(s.get('label', 'Stairs'))}
          </text>
        </g>''')
        else:
            stairs_elems.append(f'''<g class="stairs">
          <rect x="{s['x']}" y="{s['y']}" width="50" height="80" fill="#95A5A6" stroke="none"/>
          <text x="{s['x']+25}" y="{s['y']+40}" font-family="Helvetica,Arial,sans-serif" 
                font-size="12" fill="white" text-anchor="middle">
            {escape(s.get('label', 'Stairs'))}
          </text>
        </g>''')
    
    # Draw elevators
    elevator_elems = []
    for e in elevators:
        elevator_elems.append(f'''<g class="elevator">
      <rect x="{e['x']}" y="{e['y']}" width="60" height="60" fill="#34495E" 
            stroke="none" rx="2"/>
      <text x="{e['x']+30}" y="{e['y']+35}" font-family="Helvetica,Arial,sans-serif" 
            font-size="12" fill="white" text-anchor="middle" font-weight="bold">
        LIFT
      </text>
    </g>''')
    
    # Draw printers with icon
    printer_elems = []
    for p in printers:
        pos = printer_pos(p)
        label = p.get('label', p['id'])
        
        # Printer icon (simplified)
        printer_elems.append(f'''<g class="printer" data-id="{escape(p['id'])}">
      <!-- Printer icon -->
      <rect x="{pos['x']-8}" y="{pos['y']-8}" width="16" height="16" 
            fill="#2C3E50" stroke="none" rx="2"/>
      <rect x="{pos['x']-6}" y="{pos['y']-10}" width="12" height="3" 
            fill="#95A5A6" stroke="none"/>
      <rect x="{pos['x']-4}" y="{pos['y']-3}" width="8" height="5" 
            fill="white" stroke="none"/>
      <!-- Label -->
      <text x="{pos['x']}" y="{pos['y']+18}" 
            font-family="Helvetica,Arial,sans-serif" font-size="11" font-weight="500"
            fill="#2C3E50" text-anchor="middle">
        {escape(label)}
      </text>
    </g>''')
    
    # Draw entrance marker
    entrance_elem = ''
    if entrance:
        entrance_elem = f'''<g class="entrance">
      <circle cx="{entrance['x']}" cy="{entrance['y']}" r="12" 
              fill="#E74C3C" stroke="white" stroke-width="2"/>
      <text x="{entrance['x']}" y="{entrance['y']-18}" 
            font-family="Helvetica,Arial,sans-serif" font-size="12" font-weight="bold"
            fill="#E74C3C" text-anchor="middle">
        {escape(entrance.get('label', 'ENTRANCE'))}
      </text>
    </g>'''
    
    # Outer border
    border_elem = f'''<rect x="0" y="0" width="{W}" height="{H}" 
          fill="none" stroke="#333" stroke-width="4"/>'''
    
    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" 
     width="{output_width}" height="{out_h}" preserveAspectRatio="xMidYMid meet">
  <defs>
    <style>
      text {{ 
        pointer-events: none;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }}
      .room:hover rect {{ opacity: 0.9; }}
    </style>
  </defs>
  
  {chr(10).join(room_elems)}
  {chr(10).join(wall_elems)}
  {chr(10).join(door_elems)}
  {chr(10).join(window_elems)}
  {chr(10).join(stairs_elems)}
  {chr(10).join(elevator_elems)}
  {entrance_elem}
  {chr(10).join(printer_elems)}
  {border_elem}
</svg>'''
    
    return svg


def svg_to_png(svg_content, output_path, width):
    """Convert SVG to PNG using Playwright (most reliable cross-platform)
    
    Install with: pip install playwright && playwright install chromium
    Or: pip install selenium (requires Chrome browser)
    """
    
    # Try Playwright (best option - pure Python, reliable)
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
                page.set_viewport_size({"width": width, "height": int(width * 0.6)})
                page.screenshot(path=output_path, full_page=True)
                browser.close()
            return True
        finally:
            os.unlink(tmp_path)
    except ImportError:
        pass
    except Exception as e:
        print(f"Playwright error: {e}")
    
    # Try Selenium + Chrome
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
    except Exception as e:
        pass
    
    print("\nPNG conversion requires browser automation. Install ONE of:")
    print("  pip install playwright && playwright install chromium  (recommended)")
    print("  pip install selenium  (requires Chrome browser installed)")
    print("\nOr just use the SVG file - it's vector and works perfectly in web/React.")
    return False


def main():
    # Load spec from input file
    with open(INPUT_FILE, 'r') as f:
        spec = json.load(f)
    
    # Generate SVG
    svg_content = generate_floor_svg(spec, output_width=OUTPUT_WIDTH)
    
    # Save SVG
    with open(OUTPUT_SVG, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"✓ Generated: {OUTPUT_SVG}")
    
    # Save PNG
    try:
        if svg_to_png(svg_content, OUTPUT_PNG, width=OUTPUT_WIDTH):
            print(f"✓ Generated: {OUTPUT_PNG}")
        else:
            print(f"✗ PNG generation skipped")
    except Exception as e:
        print(f"✗ PNG generation failed: {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()