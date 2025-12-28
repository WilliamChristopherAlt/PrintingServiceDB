#!/usr/bin/env python3
"""
Floor Plan Generator Module
Generates SVG and PNG floor diagrams from JSON templates
"""

import json
import os
from xml.sax.saxutils import escape
from pathlib import Path

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

ROOM_TYPE_NAMES = {
    'lab': 'Computer Lab',
    'classroom': 'Lecture Hall',
    'office': 'Faculty Office',
    'library': 'Library',
    'corridor': 'Corridor',
    'restroom': 'Restroom',
    'stairs': 'Stairs',
    'elevator': 'Elevator',
    'storage': 'Storage',
    'lounge': 'Lounge'
}

BUILDING_NAMES = {
    'MAINACADE': 'Main Academic Building',
    'SCIENCE': 'Science & Technology Building',
    'LIBRARY': 'Library & Research Center'
}

OUTPUT_WIDTH = 2400


def generate_floor_svg(spec, output_width=OUTPUT_WIDTH, include_printers=False, building_name=None, floor_number=None):
    """Generate SVG from grid-based floor plan specification
    
    Args:
        spec: Floor specification dictionary
        output_width: Output width in pixels
        include_printers: If True, include printer icons. Default: False
        building_name: Name of the building for title
        floor_number: Floor number for title
    """
    
    # Grid configuration
    GRID_SIZE = spec.get('grid_size', 100)
    GRID_COLS = spec.get('grid_cols', 24)
    GRID_ROWS = spec.get('grid_rows', 14)
    
    W = GRID_COLS * GRID_SIZE
    H = GRID_ROWS * GRID_SIZE
    
    # Add space for title and legend below the diagram
    TITLE_HEIGHT = 100
    # Legend height will be calculated after we know how many room types exist
    # For now, use a reasonable estimate for initial calculation
    ESTIMATED_LEGEND_HEIGHT = 400  # Will be recalculated later
    ESTIMATED_EXTRA_HEIGHT = TITLE_HEIGHT + ESTIMATED_LEGEND_HEIGHT
    
    # Calculate output height including title and legend (will be recalculated with actual height)
    diagram_height = int(output_width * (H / W))
    out_h = diagram_height + int(output_width * (ESTIMATED_EXTRA_HEIGHT / W))
    
    rooms = spec.get('rooms', [])
    doors = spec.get('doors', [])
    printers = spec.get('printers', []) if include_printers else []
    
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
        words = label.split()
        max_word_len = max(len(word) for word in words) if words else 0
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
        # Draw corridors even without labels (they're passageways, not rooms)
        if not r['label'] and r['type'] != 'corridor':
            color = get_room_color(r['type'])
            room_elems.append(f'''<rect x="{r['x']}" y="{r['y']}" width="{r['w']}" height="{r['h']}" 
                  fill="{color}" stroke="none"/>''')
            continue
        
        # Corridors without labels should still be drawn (they're passageways)
        if not r['label'] and r['type'] == 'corridor':
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
        
        # Estimate text width (rough: ~20px per character for font-size 40)
        # Leave 40px margin on each side
        available_width = r['w'] - 80
        font_size = 40
        char_width_estimate = 20
        
        # Split text into multiple lines if needed (horizontal preferred)
        words = r['label'].split()
        full_text = r['label']
        estimated_width = len(full_text) * char_width_estimate
        
        if rotate:
            # Vertical text (rare case)
            label = f'''<text x="{cx}" y="{cy}" 
                  font-family="Roboto,Segoe UI,Arial,sans-serif" 
                  font-size="{font_size}" font-weight="600"
                  fill="{text_color}" text-anchor="middle" dominant-baseline="middle"
                  transform="rotate(-90 {cx} {cy})">
              {escape(r['label'])}
            </text>'''
        elif estimated_width > available_width and len(words) > 1:
            # Text is too wide - split into multiple lines
            line_height = 45
            max_lines = min(4, len(words))  # Max 4 lines
            
            # Smart word wrapping: try to balance lines
            lines = []
            if len(words) == 2:
                # For 2 words, check if each fits individually
                if len(words[0]) * char_width_estimate > available_width or len(words[1]) * char_width_estimate > available_width:
                    # Split each word if too long (shouldn't happen often)
                    lines = [[words[0]], [words[1]]]
                else:
                    # Try to fit both, or split if needed
                    if estimated_width > available_width:
                        lines = [[words[0]], [words[1]]]
                    else:
                        lines = [[words[0], words[1]]]
            elif len(words) == 3:
                lines = [[words[0]], [words[1]], [words[2]]]
            elif len(words) == 4:
                # Try to balance: 2+2 or 1+2+1
                if (len(words[0] + ' ' + words[1]) * char_width_estimate <= available_width and
                    len(words[2] + ' ' + words[3]) * char_width_estimate <= available_width):
                    lines = [[words[0], words[1]], [words[2], words[3]]]
                else:
                    lines = [[words[0]], [words[1], words[2]], [words[3]]]
            else:
                # For 5+ words, split into roughly equal parts
                # Try to create 2-3 balanced lines
                if len(words) <= 6:
                    # Try 2 lines
                    mid = len(words) // 2
                    line1_text = ' '.join(words[:mid])
                    line2_text = ' '.join(words[mid:])
                    if (len(line1_text) * char_width_estimate <= available_width and
                        len(line2_text) * char_width_estimate <= available_width):
                        lines = [words[:mid], words[mid:]]
                    else:
                        # Need 3 lines
                        third = len(words) // 3
                        lines = [words[:third], words[third:2*third], words[2*third:]]
                else:
                    # More than 6 words - split into 3-4 lines
                    quarter = len(words) // 4
                    if quarter > 0:
                        lines = [words[:quarter], words[quarter:2*quarter], 
                                words[2*quarter:3*quarter], words[3*quarter:]]
                    else:
                        lines = [words]
            
            # Center the text block vertically, but ensure it stays within room bounds
            num_lines = len(lines)
            total_height = (num_lines - 1) * line_height
            # Calculate text bounds to ensure it fits
            text_top_margin = 20
            text_bottom_margin = 20
            available_height = r['h'] - text_top_margin - text_bottom_margin
            
            # If text is too tall, reduce font size
            if total_height + font_size > available_height:
                font_size = max(24, int((available_height - total_height) / num_lines))
                line_height = font_size + 5
            
            start_y = r['y'] + text_top_margin + (font_size / 2)
            # Recalculate total height with adjusted font
            total_height = (num_lines - 1) * line_height
            # Center vertically within available space
            if total_height < available_height:
                start_y = r['y'] + text_top_margin + (available_height - total_height) / 2 + (font_size / 2)
            
            label = '<g>'
            for i, line_words in enumerate(lines):
                line_text = ' '.join(line_words)
                y_pos = start_y + i * line_height
                # Ensure text doesn't go below room boundary
                if y_pos + font_size/2 > r['y'] + r['h'] - text_bottom_margin:
                    break  # Skip lines that would overflow
                label += f'''<text x="{cx}" y="{y_pos}" 
                      font-family="Roboto,Segoe UI,Arial,sans-serif" 
                      font-size="{font_size}" font-weight="600"
                      fill="{text_color}" text-anchor="middle" dominant-baseline="middle">
                  {escape(line_text)}
                </text>'''
            label += '</g>'
        else:
            # Single line horizontal text - ensure proper centering and it fits
            # For very small rooms, use smaller font if needed
            text_margin = 20  # Margin on all sides
            max_font_width = r['w'] - (text_margin * 2)
            max_font_height = r['h'] - (text_margin * 2)
            
            if r['w'] < 150 or r['h'] < 150:
                # Small room - use smaller font and ensure it fits
                adjusted_font_size = min(font_size, int(max_font_width / (len(r['label']) * 0.6)), int(max_font_height * 0.8))
                if adjusted_font_size < 20:
                    adjusted_font_size = 20
            else:
                # Check if text fits, reduce font if needed
                estimated_text_width = len(r['label']) * (font_size * 0.6)
                if estimated_text_width > max_font_width:
                    adjusted_font_size = int(max_font_width / (len(r['label']) * 0.6))
                else:
                    adjusted_font_size = font_size
                # Also check height
                if adjusted_font_size > max_font_height:
                    adjusted_font_size = int(max_font_height * 0.8)
            
            # Center the text but ensure it stays within bounds
            text_y = cy
            if text_y - adjusted_font_size/2 < r['y'] + text_margin:
                text_y = r['y'] + text_margin + adjusted_font_size/2
            if text_y + adjusted_font_size/2 > r['y'] + r['h'] - text_margin:
                text_y = r['y'] + r['h'] - text_margin - adjusted_font_size/2
            
            label = f'''<text x="{cx}" y="{text_y}" 
                  font-family="Roboto,Segoe UI,Arial,sans-serif" 
                  font-size="{adjusted_font_size}" font-weight="600"
                  fill="{text_color}" text-anchor="middle" dominant-baseline="middle">
              {escape(r['label'])}
            </text>'''
        
        room_elems.append(label)
    
    # DOORS - Removed per user request (no doors in diagrams)
    
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
    
    # Building outline
    border = f'<rect x="0" y="0" width="{W}" height="{H}" fill="none" stroke="#222" stroke-width="8"/>'
    
    # Generate title and legend
    title_legend_elems = []
    
    # Title
    if building_name and floor_number:
        # Get ordinal suffix for floor number
        def get_ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return f"{n}{suffix}"
        
        title_text = f"{building_name} - {get_ordinal(floor_number)} Floor"
        title_y = H + 50
        title_legend_elems.append(f'''<text x="{W/2}" y="{title_y}" 
              font-family="Roboto,Segoe UI,Arial,sans-serif" 
              font-size="48" font-weight="700"
              fill="#1a1a1a" text-anchor="middle" dominant-baseline="middle">
          {escape(title_text)}
        </text>''')
    
    # Legend - collect unique room types from the floor
    unique_room_types = set()
    for r in rooms:
        room_type = r.get('type', 'corridor')
        if room_type in ROOM_COLORS:  # Only include types we have colors for
            unique_room_types.add(room_type)
    
    # Sort room types for consistent legend order
    legend_order = ['lab', 'classroom', 'office', 'library', 'lounge', 'restroom', 'stairs', 'elevator', 'storage', 'corridor']
    sorted_types = [t for t in legend_order if t in unique_room_types]
    
    # Calculate actual legend height based on grid layout (3 columns)
    LEGEND_COLS = 3
    LEGEND_ITEM_HEIGHT = 65  # Reduced height for better performance
    LEGEND_ITEM_WIDTH = W / LEGEND_COLS
    num_rows = (len(sorted_types) + LEGEND_COLS - 1) // LEGEND_COLS  # Ceiling division
    LEGEND_HEIGHT = num_rows * LEGEND_ITEM_HEIGHT + 40
    EXTRA_HEIGHT = TITLE_HEIGHT + LEGEND_HEIGHT
    
    # Generate legend items - GRID layout (3 per row, square on left, text on right)
    legend_start_y = H + TITLE_HEIGHT + 40
    legend_square_size = 50  # Reasonable size squares
    legend_text_size = 40  # Reasonable text size
    legend_text_margin = 20  # Space between square and text
    
    for i, room_type in enumerate(sorted_types):
        row = i // LEGEND_COLS
        col = i % LEGEND_COLS
        
        # Calculate position for this column
        col_left = col * LEGEND_ITEM_WIDTH
        col_center_x = col_left + LEGEND_ITEM_WIDTH / 2
        
        # Center the square+text group within the column
        square_x = col_center_x - (legend_square_size + legend_text_margin + 150) / 2
        text_x = square_x + legend_square_size + legend_text_margin
        
        y_pos = legend_start_y + row * LEGEND_ITEM_HEIGHT
        
        color = ROOM_COLORS.get(room_type, '#FFFFFF')
        room_name = ROOM_TYPE_NAMES.get(room_type, room_type.title())
        
        # Colored square (on the left)
        title_legend_elems.append(f'''<rect x="{square_x}" y="{y_pos - legend_square_size/2}" 
              width="{legend_square_size}" height="{legend_square_size}" 
              fill="{color}" stroke="#333" stroke-width="3"/>''')
        
        # Room name to the right of square (MUCH bigger text)
        title_legend_elems.append(f'''<text x="{text_x}" y="{y_pos}" 
              font-family="Roboto,Segoe UI,Arial,sans-serif" 
              font-size="{legend_text_size}" font-weight="700"
              fill="#1a1a1a" text-anchor="start" dominant-baseline="middle">
          {escape(room_name)}
        </text>''')
    
    # Update viewBox to include title and legend area
    total_height = H + EXTRA_HEIGHT
    
    # Recalculate output height with actual EXTRA_HEIGHT
    out_h = diagram_height + int(output_width * (EXTRA_HEIGHT / W))
    
    svg = f'''<?xml version="1.0" encoding="utf-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     viewBox="0 0 {W} {total_height}" 
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
  <rect x="0" y="0" width="{W}" height="{total_height}" fill="#f5f5f5"/>
  
  <!-- Rooms -->
  {chr(10).join(room_elems)}
  
  <!-- Printers -->
  {chr(10).join(printer_elems)}
  
  <!-- Building outline -->
  {border}
  
  <!-- Title and Legend -->
  {chr(10).join(title_legend_elems)}
</svg>'''
    
    return svg


def svg_to_png(svg_content, output_path, width=OUTPUT_WIDTH, timeout=5):
    """Convert SVG to PNG using Playwright. Returns True if successful, False otherwise."""
    import re
    import tempfile
    
    # Extract dimensions from SVG viewBox
    viewbox_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_content)
    if viewbox_match:
        svg_width = int(viewbox_match.group(1))
        svg_height = int(viewbox_match.group(2))
        # Calculate height maintaining aspect ratio
        exact_height = int(width * (svg_height / svg_width))
    else:
        # Fallback: try to get width/height attributes
        width_match = re.search(r'width="(\d+)"', svg_content)
        height_match = re.search(r'height="(\d+)"', svg_content)
        if width_match and height_match:
            svg_width = int(width_match.group(1))
            svg_height = int(height_match.group(1))
            exact_height = int(width * (svg_height / svg_width))
        else:
            exact_height = int(width * 0.583)
    
    # Method 1: Use Playwright (fast and accurate, no cropping)
    try:
        from playwright.sync_api import sync_playwright
        
        # Create temporary SVG file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name
        
        try:
            with sync_playwright() as p:
                # Launch with minimal overhead
                browser = p.chromium.launch(headless=True, args=['--disable-gpu', '--no-sandbox'])
                # Use viewport that matches desired output size
                context = browser.new_context(
                    viewport={'width': width, 'height': exact_height},
                    device_scale_factor=1,
                    ignore_https_errors=True
                )
                page = context.new_page()
                
                # Convert Windows path to file:// URL
                abs_path = os.path.abspath(tmp_path)
                file_url = f'file:///{abs_path.replace(chr(92), "/")}'
                
                # Load the SVG - use domcontentloaded for faster loading
                page.goto(file_url, wait_until='domcontentloaded', timeout=5000)
                
                # Minimal wait - SVG renders instantly
                page.wait_for_timeout(50)
                
                # Get the SVG element and screenshot it directly - much faster than full page
                svg_element = page.query_selector('svg')
                if svg_element:
                    # Screenshot the SVG element directly - fastest method
                    svg_element.screenshot(path=output_path, timeout=5000)
                else:
                    # Fallback: screenshot the entire page
                    page.screenshot(path=output_path, full_page=True, timeout=5000)
                
                browser.close()
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                    return True
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except:
                pass
    except ImportError:
        pass  # Playwright not installed
    except Exception as e:
        print(f"      Playwright failed: {e}")
        pass
    
    # Method 3: Try Selenium (last resort)
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8') as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name
        
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--hide-scrollbars')
            chrome_options.add_argument(f'--window-size={width},{exact_height}')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            
            abs_path = os.path.abspath(tmp_path)
            file_url = f'file:///{abs_path.replace(chr(92), "/")}'
            driver.get(file_url)
            driver.set_window_size(width, exact_height)
            
            import time
            time.sleep(1)
            
            try:
                svg_element = driver.find_element(By.TAG_NAME, 'svg')
                svg_element.screenshot(output_path)
            except:
                driver.save_screenshot(output_path)
            
            driver.quit()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                return True
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except:
                pass
    except ImportError:
        pass  # Selenium not installed
    except Exception:
        pass  # Selenium failed
    
    return False


def generate_floor_diagram(template_path, output_dir, building_code, floor_number, room_mapping, generate_png=True, include_printers=False):
    """
    Generate floor diagram from template and save to output directory.
    Returns tuple: (diagram_filename, grid_to_pixel_scale)
    
    Args:
        template_path: Path to JSON template file
        output_dir: Directory to save diagrams
        building_code: Code of the building
        floor_number: Floor number
        room_mapping: Dict mapping room template IDs to database room_codes
        generate_png: If True, also generate PNG. Default: True
        include_printers: If True, include printer icons. Default: False
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate deterministic filename (no hash)
    filename_base = f"{building_code}_F{floor_number}"
    svg_filename = f"{filename_base}.svg"
    png_filename = f"{filename_base}.png"
    svg_path = os.path.join(output_dir, svg_filename)
    
    # Load template (needed for scale calculation even if file exists)
    with open(template_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    # Calculate grid to pixel scale (needed regardless)
    GRID_SIZE = spec.get('grid_size', 100)
    GRID_COLS = spec.get('grid_cols', 24)
    svg_width = GRID_COLS * GRID_SIZE
    grid_to_pixel_scale = OUTPUT_WIDTH / svg_width
    
    # Get building name from building code
    building_name = BUILDING_NAMES.get(building_code, building_code)
    
    # Always regenerate SVG to include title and legend (even if files exist)
    svg_content = None
    
    # Update room labels to match database room names
    # FIRST: Remove duplicate restrooms - ensure only one men's and one women's per floor
    rooms = spec.get('rooms', [])
    seen_restrooms = {'m': False, 'w': False}  # Track to prevent duplicates
    filtered_rooms = []
    
    for room in rooms:
        room_id = room.get('id', '')
        current_label = room.get('label', '')
        room_type = room.get('type', '')
        
        # Prevent duplicate restrooms - REMOVE duplicates entirely
        if room_type == 'restroom':
            is_mens = 'restroom-m' in room_id.lower() or current_label == "Men's" or current_label == "Men"
            is_womens = 'restroom-w' in room_id.lower() or current_label == "Women's" or current_label == "Women"
            
            if is_mens:
                if seen_restrooms['m']:
                    # Duplicate men's restroom - SKIP IT ENTIRELY
                    continue
                seen_restrooms['m'] = True
            elif is_womens:
                if seen_restrooms['w']:
                    # Duplicate women's restroom - SKIP IT ENTIRELY
                    continue
                seen_restrooms['w'] = True
        
        # Room is not a duplicate, add it to filtered list
        filtered_rooms.append(room)
    
    # Update the spec with filtered rooms
    spec['rooms'] = filtered_rooms
    rooms = filtered_rooms
    
    # NOW update room labels
    for room in rooms:
        room_id = room.get('id', '')
        current_label = room.get('label', '')
        
        # Try multiple matching strategies to ensure we get a label
        # Strategy 1: Match by room ID (preferred)
        if room_id and room_id in room_mapping:
            room['label'] = room_mapping[room_id]
        # Strategy 2: Match by current label (only if ID match failed)
        elif current_label and current_label in room_mapping:
            room['label'] = room_mapping[current_label]
        # Strategy 3: If no match found, keep original label if it exists
        # (This ensures rooms still show something even if not in mapping)
    
    # Get building name from building code
    building_name = BUILDING_NAMES.get(building_code, building_code)
    
    # Generate SVG if we don't already have it
    if svg_content is None:
        svg_content = generate_floor_svg(spec, OUTPUT_WIDTH, include_printers=include_printers, 
                                         building_name=building_name, floor_number=floor_number)
    
    # Save SVG (fast)
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    
    # Generate PNG (if requested)
    png_path = os.path.join(output_dir, png_filename)
    if generate_png:
        if svg_to_png(svg_content, png_path, OUTPUT_WIDTH, timeout=3):
            # Verify PNG was created successfully
            if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
                return (png_filename, grid_to_pixel_scale)
        
        # PNG generation failed - print helpful message and raise error
        error_msg = (
            f"PNG generation failed for {building_code} F{floor_number}\n"
            f"  Install Playwright for PNG conversion: pip install playwright\n"
            f"  Then run: playwright install chromium"
        )
        print(f"    ERROR: {error_msg}")
        raise RuntimeError(error_msg)
    
    # Always return PNG filename (even if not generated yet - will be generated in batch)
    # Database should always reference PNG files, not SVG
    return (png_filename, grid_to_pixel_scale)


def get_room_grid_coordinate(room_spec, grid_rx=0.5, grid_ry=0.5):
    """
    Calculate grid coordinate for a position within a room.
    Returns tuple: (grid_x, grid_y) as floats for precise positioning
    """
    grid_x = room_spec['grid_x'] + (room_spec['grid_w'] * grid_rx)
    grid_y = room_spec['grid_y'] + (room_spec['grid_h'] * grid_ry)
    return (grid_x, grid_y)


def grid_to_image_coordinate(grid_x, grid_y, grid_to_pixel_scale):
    """
    Convert grid coordinates to image pixel coordinates.
    Returns tuple: (pixel_x, pixel_y)
    """
    pixel_x = int(grid_x * grid_to_pixel_scale)
    pixel_y = int(grid_y * grid_to_pixel_scale)
    return (pixel_x, pixel_y)

