#!/usr/bin/env python3
"""
Unified diagram renderer for pmtm_database project.
Renders all PlantUML diagrams to PNG format.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple, Optional

# Configuration
BASE_DIR = Path(__file__).parent
RENDER_METHOD = "kroki"  # Options: "kroki", "local", "plantuml"
PLANTUML_JAR_PATH = "plantuml.jar"  # Only needed for "local" method

# Diagrams to render
DIAGRAMS = [
    # Database diagrams
    {
        "name": "Database Diagram",
        "puml_file": BASE_DIR / "database" / "db_diagram.puml",
        "png_file": BASE_DIR / "database" / "db_diagram.png",
    },
    # Activity diagrams
    {
        "name": "Print Document Activity Diagram",
        "puml_file": BASE_DIR / "activity_diagrams" / "print_document_activity_diagram.puml",
        "png_file": BASE_DIR / "activity_diagrams" / "print_document_activity_diagram.png",
    },
    {
        "name": "Cancel Print Job Activity Diagram",
        "puml_file": BASE_DIR / "activity_diagrams" / "cancel_print_job_activity_diagram.puml",
        "png_file": BASE_DIR / "activity_diagrams" / "cancel_print_job_activity_diagram.png",
    },
    {
        "name": "Deposit to Account Activity Diagram",
        "puml_file": BASE_DIR / "activity_diagrams" / "deposit_to_account_activity_diagram.puml",
        "png_file": BASE_DIR / "activity_diagrams" / "deposit_to_account_activity_diagram.png",
    },
    # Sequence diagrams
    {
        "name": "Print Document Sequence Diagram",
        "puml_file": BASE_DIR / "sequence_diagrams" / "print_document_sequence_diagram.puml",
        "png_file": BASE_DIR / "sequence_diagrams" / "print_document_sequence_diagram.png",
    },
    {
        "name": "Cancel Print Job Sequence Diagram",
        "puml_file": BASE_DIR / "sequence_diagrams" / "cancel_print_job_sequence_diagram.puml",
        "png_file": BASE_DIR / "sequence_diagrams" / "cancel_print_job_sequence_diagram.png",
    },
    {
        "name": "Deposit to Account Sequence Diagram",
        "puml_file": BASE_DIR / "sequence_diagrams" / "deposit_to_account_sequence_diagram.puml",
        "png_file": BASE_DIR / "sequence_diagrams" / "deposit_to_account_sequence_diagram.png",
    },
    # Class diagrams
    {
        "name": "Print Document Class Diagram",
        "puml_file": BASE_DIR / "class_diagrams" / "print_document_class_diagram.puml",
        "png_file": BASE_DIR / "class_diagrams" / "print_document_class_diagram.png",
    },
    {
        "name": "Cancel Print Job Class Diagram",
        "puml_file": BASE_DIR / "class_diagrams" / "cancel_print_job_class_diagram.puml",
        "png_file": BASE_DIR / "class_diagrams" / "cancel_print_job_class_diagram.png",
    },
    {
        "name": "Deposit to Account Class Diagram",
        "puml_file": BASE_DIR / "class_diagrams" / "deposit_to_account_class_diagram.puml",
        "png_file": BASE_DIR / "class_diagrams" / "deposit_to_account_class_diagram.png",
    },
    # Component diagrams
    {
        "name": "Print Management Component Diagram",
        "puml_file": BASE_DIR / "component_diagrams" / "print_management_component_diagram.puml",
        "png_file": BASE_DIR / "component_diagrams" / "print_management_component_diagram.png",
    },
    # Architecture diagrams
    {
        "name": "HCMSIU-SSPS System Architecture",
        "puml_file": BASE_DIR / "architecture_diagrams" / "hcmsiu_ssps_architecture_diagram.puml",
        "png_file": BASE_DIR / "architecture_diagrams" / "hcmsiu_ssps_architecture_diagram.png",
    },
]


def render_with_kroki(puml_code: str, output_path: Path) -> Tuple[bool, Optional[str]]:
    """Render PlantUML using Kroki server (recommended - fast and reliable)."""
    try:
        import requests
        
        print("  🔄 Using Kroki server...")
        url = "https://kroki.io/plantuml/png"
        
        response = requests.post(
            url,
            data=puml_code.encode('utf-8'),
            headers={"Content-Type": "text/plain"},
            timeout=120
        )
        
        if response.status_code != 200:
            error_msg = f"Kroki server error: {response.status_code}\n{response.text[:500]}"
            return False, error_msg
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True, None
        
    except ImportError:
        return False, "requests library not installed. Run: pip install requests"
    except requests.Timeout:
        return False, "Kroki server timed out (diagram may be too large or server busy)"
    except Exception as e:
        return False, f"Kroki rendering failed: {str(e)}"


def render_with_local(puml_code: str, output_path: Path) -> Tuple[bool, Optional[str]]:
    """Render PlantUML using local PlantUML JAR (requires Java)."""
    jar_path = Path(PLANTUML_JAR_PATH)
    if not jar_path.exists():
        return False, f"PlantUML JAR not found at: {jar_path}\nDownload from: https://plantuml.com/download"
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False, encoding='utf-8') as f:
            temp_puml = f.name
            f.write(puml_code)
        
        try:
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ['java', '-Xmx2048m', '-jar', str(jar_path), '-tpng', temp_puml, '-o', str(output_dir)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                error_msg = f"PlantUML error:\n{result.stderr}"
                return False, error_msg
            
            # Find generated PNG
            temp_png = temp_puml.replace('.puml', '.png')
            if os.path.exists(temp_png):
                os.replace(temp_png, output_path)
                return True, None
            else:
                return False, "PNG file was not generated"
                
        finally:
            if os.path.exists(temp_puml):
                os.unlink(temp_puml)
                
    except subprocess.TimeoutExpired:
        return False, "PlantUML execution timed out"
    except FileNotFoundError:
        return False, "Java not found. Please install Java to use local rendering."
    except Exception as e:
        return False, f"Local rendering failed: {str(e)}"


def render_with_plantuml_server(puml_code: str, output_path: Path) -> Tuple[bool, Optional[str]]:
    """Render PlantUML using official PlantUML server (slow but no setup required)."""
    try:
        import requests
        import zlib
        import base64
        
        # PlantUML encoding
        PLANTUML_ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
        
        def encode_6bit(b):
            if b < 64:
                return PLANTUML_ALPHABET[b]
            return '?'
        
        def append_3bytes(b1, b2, b3):
            c1 = b1 >> 2
            c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
            c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
            c4 = b3 & 0x3F
            return (encode_6bit(c1 & 0x3F) + encode_6bit(c2 & 0x3F) +
                    encode_6bit(c3 & 0x3F) + encode_6bit(c4 & 0x3F))
        
        utf8_bytes = puml_code.encode('utf-8')
        compress_obj = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
        compressed = compress_obj.compress(utf8_bytes)
        compressed += compress_obj.flush()
        
        result = []
        for i in range(0, len(compressed), 3):
            b1 = compressed[i]
            b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
            b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
            result.append(append_3bytes(b1, b2, b3))
        
        encoded = ''.join(result)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True, None
        
    except ImportError:
        return False, "requests library not installed. Run: pip install requests"
    except requests.Timeout:
        return False, "PlantUML server timed out"
    except Exception as e:
        return False, f"PlantUML server rendering failed: {str(e)}"


def render_diagram(puml_file: Path, png_file: Path) -> Tuple[bool, Optional[str]]:
    """Render a single PlantUML diagram to PNG."""
    if not puml_file.exists():
        return False, f"PlantUML file not found: {puml_file}"
    
    print(f"  📖 Reading: {puml_file.name}")
    try:
        with open(puml_file, 'r', encoding='utf-8') as f:
            puml_code = f.read()
    except Exception as e:
        return False, f"Failed to read PlantUML file: {str(e)}"
    
    # Validate PlantUML syntax (basic check)
    if "@startuml" not in puml_code or "@enduml" not in puml_code:
        return False, "Invalid PlantUML file: missing @startuml or @enduml"
    
    # Render based on method
    if RENDER_METHOD == "kroki":
        success, error = render_with_kroki(puml_code, png_file)
    elif RENDER_METHOD == "local":
        success, error = render_with_local(puml_code, png_file)
    elif RENDER_METHOD == "plantuml":
        success, error = render_with_plantuml_server(puml_code, png_file)
    else:
        return False, f"Unknown render method: {RENDER_METHOD}"
    
    if success:
        file_size = png_file.stat().st_size / 1024  # KB
        print(f"  ✅ Rendered: {png_file.name} ({file_size:.1f} KB)")
        return True, None
    else:
        return False, error


def main():
    """Main function to render all diagrams."""
    print("=" * 70)
    print("PlantUML Diagram Renderer")
    print("=" * 70)
    print(f"Render method: {RENDER_METHOD}")
    print(f"Base directory: {BASE_DIR}")
    print()
    
    success_count = 0
    failed_diagrams = []
    
    for diagram in DIAGRAMS:
        print(f"\n📊 Rendering: {diagram['name']}")
        print(f"   Input:  {diagram['puml_file'].name}")
        print(f"   Output: {diagram['png_file'].name}")
        
        success, error = render_diagram(diagram['puml_file'], diagram['png_file'])
        
        if success:
            success_count += 1
        else:
            failed_diagrams.append((diagram['name'], error))
            print(f"  ❌ Failed: {error}")
    
    # Summary
    print()
    print("=" * 70)
    print(f"Summary: {success_count}/{len(DIAGRAMS)} diagrams rendered successfully")
    
    if failed_diagrams:
        print("\n❌ Failed diagrams:")
        for name, error in failed_diagrams:
            print(f"  - {name}")
            print(f"    Error: {error}")
        print("\n💡 Suggestions:")
        print("  1. Check PlantUML syntax in .puml files")
        print("  2. Try different RENDER_METHOD (kroki, local, plantuml)")
        print("  3. For local method: ensure Java and plantuml.jar are installed")
        print("  4. For server methods: check internet connection")
        return 1
    else:
        print("\n✅ All diagrams rendered successfully!")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

