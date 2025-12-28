import re
import zlib
import requests
import base64
from collections import defaultdict
from PIL import Image
from io import BytesIO

# ============================================================
# FILE PATHS - CONFIGURE THESE
# ============================================================
INPUT_SQL_FILE = r'pmtm_database\sql\design.sql'
OUTPUT_PLANTUML_FILE = r'pmtm_database\visualize\db_diagram.puml'
OUTPUT_PNG_FILE = r'pmtm_database\visualize\db_diagram.png'

# ============================================================
# RENDERING OPTIONS
# ============================================================
# Choose rendering method:
# 1. "local" - Use local PlantUML JAR (requires Java + plantuml.jar)
# 2. "kroki" - Use Kroki public server (faster, more reliable)
# 3. "plantuml" - Use official PlantUML server (original, but slow)
RENDER_METHOD = "kroki"

# Path to PlantUML JAR file (only needed if RENDER_METHOD = "local")
PLANTUML_JAR_PATH = r"plantuml.jar"

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


def generate_png_from_plantuml(puml_code, output_path):
    """
    Generate diagram PNG from PlantUML code using configured method.
    Returns (success, width, height)
    """
    if RENDER_METHOD == "local":
        return generate_png_local(puml_code, output_path)
    elif RENDER_METHOD == "kroki":
        return generate_png_kroki(puml_code, output_path)
    else:  # plantuml
        return generate_png_plantuml_server(puml_code, output_path)


def generate_png_local(puml_code, output_path):
    """Generate PNG using local PlantUML JAR file (requires Java)"""
    import subprocess
    import tempfile
    import os
    
    try:
        print("  🔄 Using local PlantUML JAR...")
        
        # Check if JAR exists
        if not os.path.exists(PLANTUML_JAR_PATH):
            print(f"  ❌ PlantUML JAR not found at: {PLANTUML_JAR_PATH}")
            print("  💡 Download from: https://plantuml.com/download")
            return False, None, None
        
        # Create temp file for PlantUML code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False, encoding='utf-8') as f:
            temp_puml = f.name
            f.write(puml_code)
        
        try:
            # Run PlantUML
            print("  🏃 Running PlantUML...")
            result = subprocess.run(
                ['java', '-jar', PLANTUML_JAR_PATH, '-tpng', temp_puml, '-o', os.path.dirname(os.path.abspath(output_path))],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"  ❌ PlantUML error: {result.stderr}")
                return False, None, None
            
            # Move generated file to desired location
            temp_png = temp_puml.replace('.puml', '.png')
            if os.path.exists(temp_png):
                os.replace(temp_png, output_path)
            
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    width, height = get_image_dimensions(f.read())
                print(f"  ✅ PNG generated successfully ({width}x{height})")
                return True, width, height
            else:
                print("  ❌ PNG file not created")
                return False, None, None
                
        finally:
            # Cleanup temp file
            if os.path.exists(temp_puml):
                os.unlink(temp_puml)
                
    except subprocess.TimeoutExpired:
        print("  ❌ PlantUML execution timed out")
        return False, None, None
    except FileNotFoundError:
        print("  ❌ Java not found. Please install Java to use local rendering.")
        return False, None, None
    except Exception as e:
        print(f"  ❌ Failed to generate PNG locally: {e}")
        return False, None, None


def generate_png_kroki(puml_code, output_path):
    """Generate PNG using Kroki server (more reliable than PlantUML server)"""
    try:
        print("  🔄 Using Kroki server (faster alternative)...")
        
        # Use POST method with plain text body
        url = "https://kroki.io/plantuml/png"
        
        print(f"  🌐 Sending diagram to Kroki server (POST method)...")
        response = requests.post(
            url,
            data=puml_code.encode('utf-8'),
            headers={"Content-Type": "text/plain"},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"  ❌ Kroki server error: {response.status_code}")
            print(f"  📝 Error details: {response.text[:500]}")
            return False, None, None
        
        response.raise_for_status()
        
        image_data = response.content
        width, height = get_image_dimensions(image_data)
        
        print(f"  💾 Saving PNG to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"  ✅ PNG saved successfully ({width}x{height})")
        return True, width, height
    except requests.Timeout:
        print(f"  ❌ Kroki server timed out (diagram may be too large)")
        return False, None, None
    except requests.HTTPError as e:
        print(f"  ❌ Kroki server error: {e}")
        if e.response.status_code == 400:
            print(f"  💡 The diagram may have syntax errors. Check the .puml file.")
        return False, None, None
    except Exception as e:
        print(f"  ❌ Failed to generate PNG via Kroki: {e}")
        return False, None, None


def generate_png_plantuml_server(puml_code, output_path):
    """Generate PNG using official PlantUML server (original method)"""
    try:
        print("  🔄 Using official PlantUML server...")
        print("  ⚠️  Note: This server can be slow. Try RENDER_METHOD='kroki' for faster results.")
        
        encoded = plantuml_encode(puml_code)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        print(f"  🌐 Fetching diagram from PlantUML server...")
        response = requests.get(url, timeout=90)  # Increased timeout
        response.raise_for_status()
        
        image_data = response.content
        width, height = get_image_dimensions(image_data)
        
        print(f"  💾 Saving PNG to: {output_path}")
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        print(f"  ✅ PNG saved successfully ({width}x{height})")
        return True, width, height
    except requests.Timeout:
        print(f"  ❌ PlantUML server timed out after 90 seconds")
        print(f"  💡 Try RENDER_METHOD='kroki' or 'local' instead")
        return False, None, None
    except Exception as e:
        print(f"  ❌ Failed to generate PNG: {e}")
        return False, None, None

# ============================================================
# SQL PARSER (handles composite foreign keys)
# ============================================================

def parse_sql_schema(sql_content):
    tables = {}
    relationships = []

    # Remove comments
    sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)

    # Match CREATE TABLE statements (handle both regular names and bracketed names like [user])
    table_pattern = r'CREATE\s+TABLE\s+(?:\[(\w+)\]|(\w+))\s*\((.*?)\)\s*;'
    for match in re.finditer(table_pattern, sql_content, re.DOTALL | re.IGNORECASE):
        # Handle both bracketed [table] and regular table names
        table_name = match.group(1) if match.group(1) else match.group(2)
        table_body = match.group(3)
        columns = []
        lines, current_line, paren_depth = [], "", 0

        # Split by commas, ignoring those inside parentheses
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

        for line in lines:
            if not line:
                continue

            # Composite and single-column FK support (handle bracketed table names)
            fk = re.search(
                r'FOREIGN\s+KEY\s*\(\s*([^)]+?)\s*\)\s*REFERENCES\s+(?:\[(\w+)\]|(\w+))\s*\(\s*([^)]+?)\s*\)',
                line, re.IGNORECASE
            )
            if fk:
                from_cols = ','.join(c.strip() for c in fk.group(1).split(','))
                to_table = (fk.group(2) if fk.group(2) else fk.group(3)).strip()
                to_cols = ','.join(c.strip() for c in fk.group(4).split(','))
                relationships.append((table_name, from_cols, to_table, to_cols))
                continue

            # Regular column
            m = re.match(r'(\w+)\s+', line)
            if m:
                columns.append(m.group(1))

        tables[table_name] = columns

    return tables, relationships

# ============================================================
# LEVEL DETERMINATION
# ============================================================

def determine_table_levels(tables, relationships):
    """Compute topological levels with parents (referenced tables) on top"""
    dependents = defaultdict(set)
    for from_table, _, to_table, _ in relationships:
        if from_table != to_table:
            dependents[to_table].add(from_table)  # reverse dependency

    levels = {}
    processed = set()

    roots = [t for t in tables if t not in dependents or not dependents[t]]
    for t in roots:
        levels[t] = 0
        processed.add(t)

    changed = True
    while changed and len(processed) < len(tables):
        changed = False
        for t in tables:
            if t in processed:
                continue
            parents = [p for p, _, c, _ in relationships if c == t]
            if parents and all(p in levels for p in parents):
                levels[t] = max(levels[p] for p in parents) + 1
                processed.add(t)
                changed = True

    for t in tables:
        if t not in levels:
            levels[t] = 0
    return levels


# ============================================================
# PLANTUML GENERATOR
# ============================================================

# PlantUML reserved keywords that need to be escaped
PLANTUML_RESERVED = {
    'abstract', 'actor', 'agent', 'artifact', 'as', 'boundary', 'card', 'case', 
    'class', 'cloud', 'collections', 'component', 'control', 'database', 'default',
    'else', 'elseif', 'end', 'endif', 'entity', 'enum', 'extends', 'file', 'folder',
    'for', 'frame', 'function', 'group', 'if', 'implements', 'interface', 'label',
    'namespace', 'node', 'object', 'package', 'participant', 'queue', 'rectangle',
    'repeat', 'return', 'stack', 'start', 'state', 'stop', 'storage', 'switch',
    'then', 'usecase', 'user', 'while', 'type', 'order', 'left', 'right', 'up', 'down'
}

def escape_name(name):
    """Escape name if it's a PlantUML reserved keyword or contains special chars"""
    name_lower = name.lower()
    # Check if it's a reserved keyword
    if name_lower in PLANTUML_RESERVED:
        return f'"{name}"'
    # Check if it contains special characters
    if not name.replace('_', '').isalnum():
        return f'"{name}"'
    return name

def generate_plantuml(tables, relationships):
    lines = [
        "@startuml",
        "!theme plain",
        "top to bottom direction",
        "skinparam classAttributeIconSize 0",
        "skinparam linetype ortho",
        "",
        "skinparam class {",
        "  BackgroundColor LightBlue",
        "  BorderColor Blue",
        "}",
        ""
    ]

    levels = determine_table_levels(tables, relationships)
    tables_by_level = defaultdict(list)
    for t, lvl in levels.items():
        tables_by_level[lvl].append(t)

    # Classes by level
    for lvl in sorted(tables_by_level.keys()):
        lines.append(f"' Level {lvl} tables")
        for t in sorted(tables_by_level[lvl]):
            escaped_name = escape_name(t)
            lines.append(f"class {escaped_name} {{")
            for c in tables[t]:
                # Column names don't need escaping inside class body
                lines.append(f"  {c}")
            lines.append("}")
        lines.append("")

    # Relationships (no labels)
    lines.append("' Relationships")
    seen = set()
    for f, _, t, _ in relationships:
        if f != t and (f, t) not in seen:
            escaped_from = escape_name(f)
            escaped_to = escape_name(t)
            lines.append(f"{escaped_to} <-- {escaped_from}")
            seen.add((f, t))

    lines.append("@enduml")
    return "\n".join(lines)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("SQL to PlantUML Diagram Generator with PNG Export")
        print("=" * 60)
        print()
        
        # Step 1: Parse SQL
        print(f"📖 Reading SQL file: {INPUT_SQL_FILE}")
        with open(INPUT_SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("🔍 Parsing SQL schema...")
        tables, rels = parse_sql_schema(sql)
        print(f"   Found {len(tables)} tables and {len(rels)} relationships")
        print()
        
        # Step 2: Generate PlantUML code
        print("📝 Generating PlantUML code...")
        puml = generate_plantuml(tables, rels)
        
        # Step 3: Save PlantUML file
        print(f"💾 Saving PlantUML file: {OUTPUT_PLANTUML_FILE}")
        with open(OUTPUT_PLANTUML_FILE, 'w', encoding='utf-8') as f:
            f.write(puml)
        print("   ✅ PlantUML file saved")
        print()
        
        # Step 4: Generate and save PNG
        print("🖼️  Generating PNG diagram...")
        success, width, height = generate_png_from_plantuml(puml, OUTPUT_PNG_FILE)
        
        print()
        print("=" * 60)
        if success:
            print("✅ SUCCESS! Diagram generated successfully")
            print(f"   📄 PlantUML: {OUTPUT_PLANTUML_FILE}")
            print(f"   🖼️  PNG Image: {OUTPUT_PNG_FILE} ({width}x{height})")
            print("   📐 Root tables now appear at the top.")
            print(f"   🔧 Render method: {RENDER_METHOD}")
        else:
            print("⚠️  PlantUML file saved, but PNG generation failed")
            print(f"   📄 PlantUML: {OUTPUT_PLANTUML_FILE}")
            print()
            print("💡 Try these solutions:")
            print("   1. Change RENDER_METHOD to 'kroki' (recommended - faster & more reliable)")
            print("   2. Change RENDER_METHOD to 'local' (requires Java + plantuml.jar)")
            print("   3. Manually render: https://www.plantuml.com/plantuml/uml/")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR occurred:")
        print(f"   {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()