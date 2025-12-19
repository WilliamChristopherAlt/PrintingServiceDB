#!/usr/bin/env python3
"""
Smart Printing Service System (SSPS) Module Diagram Generator
============================================================
Generates PlantUML diagrams for each functional module of the database schema.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import requests
import zlib
from PIL import Image
from io import BytesIO

# ============================================================
# FILE PATHS - CONFIGURE THESE
# ============================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SQL_FILE_PATH = os.path.join(PROJECT_ROOT, 'sql', 'design.sql')
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, 'visualize', 'modules')

# ============================================================
# CONFIGURATION FLAGS
# ============================================================
SAVE_PUML_FILES = False  # Set to False to skip saving .puml files

# ============================================================
# PLANTUML ENCODING & SERVER API
# ============================================================

def plantuml_encode(plantuml_text):
    """
    Encode PlantUML text for URL using PlantUML's custom encoding.
    
    This follows PlantUML's standard encoding:
    1. UTF-8 encode the text
    2. DEFLATE compress (raw, without zlib wrapper)
    3. Encode using PlantUML's custom base64-like alphabet
    """
    # PlantUML uses a custom alphabet (not standard base64)
    PLANTUML_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    
    def encode_6bit(b):
        """Encode a 6-bit value using PlantUML alphabet"""
        if b < 64:
            return PLANTUML_ALPHABET[b]
        return '?'
    
    def append_3bytes(b1, b2, b3):
        """Encode 3 bytes into 4 characters"""
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        
        return (encode_6bit(c1 & 0x3F) +
                encode_6bit(c2 & 0x3F) +
                encode_6bit(c3 & 0x3F) +
                encode_6bit(c4 & 0x3F))
    
    # Step 1: UTF-8 encode
    utf8_bytes = plantuml_text.encode('utf-8')
    
    # Step 2: DEFLATE compress (raw deflate, without zlib wrapper)
    compress_obj = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compress_obj.compress(utf8_bytes)
    compressed += compress_obj.flush()
    
    # Step 3: Custom base64-like encoding
    result = []
    for i in range(0, len(compressed), 3):
        b1 = compressed[i]
        b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
        b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
        result.append(append_3bytes(b1, b2, b3))
    
    return ''.join(result)


def get_image_dimensions(image_data):
    """
    Get dimensions of image from bytes.
    Returns (width, height) or (None, None) if failed.
    """
    try:
        img = Image.open(BytesIO(image_data))
        return img.size  # (width, height)
    except Exception as e:
        print(f"    ⚠️  Failed to get image dimensions: {e}")
        return None, None


def generate_diagram_from_code(puml_code, output_path=None):
    """
    Generate diagram PNG from PlantUML code using online server.
    Returns (success, image_data, width, height)
    - success: True if successful, False otherwise
    - image_data: raw image bytes
    - width, height: image dimensions
    """
    try:
        encoded = plantuml_encode(puml_code)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        image_data = response.content
        width, height = get_image_dimensions(image_data)
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(image_data)
        
        return True, image_data, width, height
    except Exception as e:
        print(f"    ⚠️  Failed to generate PNG: {e}")
        return False, None, None, None


# ============================================================
# MODULE DEFINITIONS
# ============================================================

def get_predefined_modules() -> Dict[str, List[str]]:
    """
    Define all modules based on the database schema functionality.
    Each module represents a functional area of the Smart Printing Service System.
    Module names are in Vietnamese, but table names remain in English.
    """
    return {
        "Quản lý Người dùng & Xác thực": [
            'user', 'student', 'staff', 'refresh_token', 'password_reset_token'
        ],
        "Cơ cấu Học thuật": [
            'faculty', 'department', 'major', 'class', 'academic_year', 'semester'
        ],
        "Quản lý Tòa nhà & Vị trí": [
            'building', 'floor', 'room'
        ],
        "Quản lý Máy in": [
            'brand', 'printer_model', 'printer_physical', 'page_size'
        ],
        "Quản lý Công việc In": [
            'print_job', 'print_job_page', 'student', 'printer_physical', 'page_size', 'page_size_price', 'refund_print_job'
        ],
        "Quản lý Thanh toán & Số dư": [
            'deposit', 'deposit_bonus_package', 'payment', 'semester_bonus', 
            'student_semester_bonus', 'student', 'print_job', 'refund_print_job'
        ],
        "Cấu hình Giá": [
            'color_mode', 'color_mode_price', 'page_size_price', 'page_discount_package', 'page_size', 'print_job'
        ],
        "Mua giấy & Quản lý Kho": [
            'fund_source', 'supplier_paper_purchase', 'paper_purchase_item', 
            'page_size', 'staff'
        ],
        "Cấu hình Hệ thống": [
            'system_configuration', 'permitted_file_type', 'staff'
        ],
        "Kiểm tra & Ghi nhật ký": [
            'printer_log', 'system_audit_log', 'user', 'printer_physical', 'print_job'
        ]
    }


# ============================================================
# SQL PARSER
# ============================================================

def parse_sql_schema(sql_content: str) -> Tuple[Dict[str, List[str]], List[Tuple[str, str, str, str]]]:
    """
    Parse SQL schema and extract tables with columns and relationships.
    Returns (tables_dict, relationships_list)
    """
    tables = {}
    relationships = []
    
    # Remove comments
    sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
    
    # Extract CREATE TABLE statements
    # Handle SQL Server syntax with brackets: CREATE TABLE [user] or CREATE TABLE user
    table_pattern = r'CREATE TABLE\s+(?:\[?(\w+)\]?)\s*\((.*?)\);'
    
    for match in re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE):
        table_name = match.group(1).lower()
        table_body = match.group(2)
        columns = []
        
        # Parse lines
        lines = []
        current_line = ""
        paren_depth = 0
        
        for char in table_body:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                lines.append(current_line.strip())
                current_line = ""
                continue
            current_line += char
        
        if current_line.strip():
            lines.append(current_line.strip())
        
        # Process each line
        for line in lines:
            if not line:
                continue
            
            # Extract foreign keys - handle both formats
            # FOREIGN KEY (col) REFERENCES table(col)
            # FOREIGN KEY (col) REFERENCES [table](col)
            fk = re.search(
                r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s+(?:\[?(\w+)\]?)\s*\((\w+)\)', 
                line, 
                re.IGNORECASE
            )
            if fk:
                relationships.append((table_name, fk.group(1), fk.group(2).lower(), fk.group(3)))
                continue
            
            # Skip constraints
            if re.match(r'(CONSTRAINT|PRIMARY|UNIQUE|CHECK|INDEX)\b', line, re.IGNORECASE):
                continue
            
            # Extract column name - handle brackets
            col_match = re.match(r'(?:\[?(\w+)\]?)\s+', line)
            if col_match:
                columns.append(col_match.group(1))
        
        tables[table_name] = columns
    
    return tables, relationships


# ============================================================
# PLANTUML GENERATOR
# ============================================================

def generate_module_plantuml(
    module_name: str,
    module_tables: List[str],
    all_tables: Dict[str, List[str]],
    all_relationships: List[Tuple[str, str, str, str]],
    direction: str = "left to right"
) -> str:
    """
    Generate PlantUML code for a specific module.
    Only includes relationships between tables within the module.
    
    Args:
        direction: "left to right" or "top to bottom"
    """
    lines = [
        "@startuml",
        f"title {module_name}",
        "!theme plain",
        f"{direction} direction",
        "skinparam classAttributeIconSize 0",
        "skinparam linetype ortho",
        "",
        "skinparam class {",
        "  BackgroundColor LightBlue",
        "  BorderColor Blue",
        "}",
        ""
    ]
    
    # Columns to exclude
    EXCLUDED_COLUMNS = {
        'created_at', 'updated_at', 'created_by', 'updated_by', 
        'is_deleted', 'is_active', 'action_timestamp'
    }
    
    module_table_set = set(module_tables)
    
    # Add tables
    for table in sorted(module_tables):
        if table in all_tables:
            lines.append(f"class {table} {{")
            for col in all_tables[table]:
                if col not in EXCLUDED_COLUMNS:
                    lines.append(f"  {col}")
            lines.append("}")
        else:
            # Table mentioned in doc but not in SQL
            lines.append(f"class {table} {{")
            lines.append(f"  (table not found in schema)")
            lines.append("}")
    
    lines.append("")
    lines.append("' Relationships (within module only)")
    
    # Add relationships only between tables in this module
    seen = set()
    for from_table, _, to_table, _ in all_relationships:
        if from_table in module_table_set and to_table in module_table_set:
            if from_table != to_table and (from_table, to_table) not in seen:
                lines.append(f"{to_table} <-- {from_table}")
                seen.add((from_table, to_table))
    
    lines.append("")
    lines.append("@enduml")
    
    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================

def main():
    print(f"Reading SQL schema: {SQL_FILE_PATH}")
    
    # Parse SQL schema
    try:
        with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: SQL file not found at {SQL_FILE_PATH}")
        return
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return
    
    all_tables, all_relationships = parse_sql_schema(sql_content)
    print(f"Found {len(all_tables)} tables in SQL schema")
    print()
    
    # Get modules
    modules = get_predefined_modules()
    print(f"Found {len(modules)} modules:")
    for module_name, tables in modules.items():
        print(f"  - {module_name}: {len(tables)} tables")
    print()
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Generate PlantUML for each module
    print("Generating PlantUML diagrams...")
    if SAVE_PUML_FILES:
        print("📝 PUML files: ENABLED")
    else:
        print("📝 PUML files: DISABLED")
    print()
    
    successful_pngs = 0
    failed_pngs = 0
    lr_chosen = 0  # left-to-right chosen
    tb_chosen = 0  # top-to-bottom chosen
    
    for i, (module_name, module_tables) in enumerate(modules.items(), 1):
        print(f"[{i}/{len(modules)}] Processing: {module_name}")
        
        # Create safe filename
        safe_name = re.sub(r'[^\w\s-]', '', module_name)
        safe_name = re.sub(r'[-\s]+', '_', safe_name)
        
        puml_file = os.path.join(OUTPUT_FOLDER, f"{i:02d}_{safe_name}.puml")
        png_file = os.path.join(OUTPUT_FOLDER, f"{i:02d}_{safe_name}.png")
        
        # Step 1: Generate with left-to-right orientation
        print(f"  🔄 Testing left-to-right orientation...")
        puml_lr = generate_module_plantuml(
            module_name,
            module_tables,
            all_tables,
            all_relationships,
            direction="left to right"
        )
        
        success_lr, image_lr, width_lr, height_lr = generate_diagram_from_code(puml_lr)
        
        if not success_lr:
            print(f"  ❌ Failed to generate left-to-right diagram")
            failed_pngs += 1
            continue
        
        print(f"  📐 Left-to-right: {width_lr}x{height_lr}, ratio: {width_lr/height_lr:.2f}")
        
        # Step 2: Generate with top-to-bottom orientation
        print(f"  🔄 Testing top-to-bottom orientation...")
        puml_tb = generate_module_plantuml(
            module_name,
            module_tables,
            all_tables,
            all_relationships,
            direction="top to bottom"
        )
        
        success_tb, image_tb, width_tb, height_tb = generate_diagram_from_code(puml_tb)
        
        if not success_tb:
            print(f"  ⚠️  Top-to-bottom generation failed, using left-to-right")
            chosen_puml = puml_lr
            chosen_image = image_lr
            chosen_orientation = "left-to-right"
            lr_chosen += 1
        else:
            print(f"  📐 Top-to-bottom: {width_tb}x{height_tb}, ratio: {width_tb/height_tb:.2f}")
            
            # Step 3: Compare width/height ratios and choose the higher one
            ratio_lr = width_lr / height_lr if height_lr > 0 else 0
            ratio_tb = width_tb / height_tb if height_tb > 0 else 0
            
            if ratio_lr >= ratio_tb:
                chosen_puml = puml_lr
                chosen_image = image_lr
                chosen_orientation = "left-to-right"
                lr_chosen += 1
                print(f"  ✅ Chose left-to-right (ratio {ratio_lr:.2f} >= {ratio_tb:.2f})")
            else:
                chosen_puml = puml_tb
                chosen_image = image_tb
                chosen_orientation = "top-to-bottom"
                tb_chosen += 1
                print(f"  ✅ Chose top-to-bottom (ratio {ratio_tb:.2f} > {ratio_lr:.2f})")
        
        # Step 4: Save final PNG
        with open(png_file, 'wb') as f:
            f.write(chosen_image)
        print(f"  💾 Saved PNG: {png_file}")
        successful_pngs += 1
        
        # Step 5: Save PUML file if flag is enabled
        if SAVE_PUML_FILES:
            with open(puml_file, 'w', encoding='utf-8') as f:
                f.write(chosen_puml)
            print(f"  💾 Saved PUML: {puml_file}")
        
        print()
    
    # Summary
    print("=" * 60)
    print(f"✅ Done! Generated {len(modules)} PlantUML diagrams in {OUTPUT_FOLDER}")
    if SAVE_PUML_FILES:
        print(f"   📝 PUML files: {len(modules)} saved")
    else:
        print(f"   📝 PUML files: skipped (SAVE_PUML_FILES = False)")
    print(f"   📊 PNG diagrams: {successful_pngs} successful, {failed_pngs} failed")
    print(f"   🔄 Orientation selection:")
    print(f"      - Left-to-right: {lr_chosen} diagrams")
    print(f"      - Top-to-bottom: {tb_chosen} diagrams")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

