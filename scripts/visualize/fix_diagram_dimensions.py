#!/usr/bin/env python3
"""
Automatically fixes PlantUML diagram dimensions by checking rendered image size
and adjusting the PlantUML code until dimensions are acceptable.
"""

import os
import re
import sys
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
from typing import Tuple, Optional

# Configuration
BASE_DIR = Path(__file__).parent
MAX_WIDTH = 2000  # Maximum acceptable width in pixels
MAX_HEIGHT = 3000  # Maximum acceptable height in pixels
MAX_ITERATIONS = 5  # Maximum number of fix attempts

RENDER_METHOD = "kroki"  # Use Kroki server for rendering


def render_with_kroki(puml_content: str) -> Optional[bytes]:
    """Render PlantUML diagram using Kroki server."""
    import base64
    import zlib
    import urllib.request
    import urllib.parse

    # Compress and encode PlantUML content
    compressed = zlib.compress(puml_content.encode('utf-8'), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    
    # Remove padding
    encoded = encoded.rstrip('=')
    
    # Replace characters for URL
    encoded = encoded.replace('+', '-').replace('/', '_')
    
    url = f"https://kroki.io/plantuml/png/{encoded}"
    
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read()
    except Exception as e:
        print(f"  ❌ Error rendering: {e}")
        return None


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """Get width and height of PNG image."""
    from io import BytesIO
    img = Image.open(BytesIO(image_data))
    return img.size  # Returns (width, height)


def read_puml_file(file_path: Path) -> str:
    """Read PlantUML file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_puml_file(file_path: Path, content: str):
    """Write PlantUML file content."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def fix_diagram_layout(puml_content: str, iteration: int) -> str:
    """Fix diagram layout based on iteration number."""
    lines = puml_content.split('\n')
    new_lines = []
    
    # Strategy 1: Change direction
    if iteration == 1:
        # Try left to right instead of top to bottom
        for line in lines:
            if re.match(r'^\s*(top to bottom|left to right)\s+direction', line):
                new_lines.append('left to right direction')
            else:
                new_lines.append(line)
    
    # Strategy 2: Simplify interface connections
    elif iteration == 2:
        # Remove interface circles, use direct connections
        skip_interface_defs = False
        for i, line in enumerate(lines):
            # Skip interface definitions
            if 'interface "' in line and 'as ' in line:
                continue
            # Skip interface connections (lollipops)
            if re.search(r'-\s*(up|down|left|right)\s*-', line):
                continue
            # Skip socket connections
            if re.search(r'\.(r|l|u|d)\.>', line):
                continue
            # Replace with direct connections
            if 'BackendAPI_IF' in line or 'PrintService_IF' in line:
                # Convert to direct component connections
                if 'BackendAPI_IF .r.> PrintService_IF' in line:
                    new_lines.append('BackendAPI --> PrintService : uses')
                elif 'BackendAPI_IF .r.> PricingService_IF' in line:
                    new_lines.append('BackendAPI --> PricingService : uses')
                elif 'BackendAPI_IF .r.> PaymentService_IF' in line:
                    new_lines.append('BackendAPI --> PaymentService : uses')
                elif 'BackendAPI_IF .r.> RefundService_IF' in line:
                    new_lines.append('BackendAPI --> RefundService : uses')
                elif 'BackendAPI_IF .r.> DepositService_IF' in line:
                    new_lines.append('BackendAPI --> DepositService : uses')
                elif 'BackendAPI_IF .r.> BonusService_IF' in line:
                    new_lines.append('BackendAPI --> BonusService : uses')
                elif 'BackendAPI_IF .r.> LedgerService_IF' in line:
                    new_lines.append('BackendAPI --> LedgerService : uses')
                else:
                    new_lines.append(line)
            elif 'PrintService_IF' in line:
                if '.r.> PricingService_IF' in line:
                    new_lines.append('PrintService --> PricingService : uses')
                elif '.r.> PaymentService_IF' in line:
                    new_lines.append('PrintService --> PaymentService : uses')
                elif '.r.> PrinterController_IF' in line:
                    new_lines.append('PrintService --> PrinterController : uses')
                elif '.r.> FileStorage_IF' in line:
                    new_lines.append('PrintService --> FileStorage : uses')
                elif '.r.> DataAccess_IF' in line:
                    new_lines.append('PrintService --> Database : uses')
                else:
                    new_lines.append(line)
            elif 'PricingService_IF' in line and '.r.> DataAccess_IF' in line:
                new_lines.append('PricingService --> Database : uses')
            elif 'PaymentService_IF' in line:
                if '.r.> LedgerService_IF' in line:
                    new_lines.append('PaymentService --> LedgerService : uses')
                elif '.r.> PaymentGateway_IF' in line:
                    new_lines.append('PaymentService --> PaymentGateway : uses')
                elif '.r.> DataAccess_IF' in line:
                    new_lines.append('PaymentService --> Database : uses')
                else:
                    new_lines.append(line)
            elif 'RefundService_IF' in line:
                if '.r.> PaymentService_IF' in line:
                    new_lines.append('RefundService --> PaymentService : uses')
                elif '.r.> LedgerService_IF' in line:
                    new_lines.append('RefundService --> LedgerService : uses')
                elif '.r.> DataAccess_IF' in line:
                    new_lines.append('RefundService --> Database : uses')
                else:
                    new_lines.append(line)
            elif 'DepositService_IF' in line:
                if '.r.> BonusService_IF' in line:
                    new_lines.append('DepositService --> BonusService : uses')
                elif '.r.> PaymentGateway_IF' in line:
                    new_lines.append('DepositService --> PaymentGateway : uses')
                elif '.r.> LedgerService_IF' in line:
                    new_lines.append('DepositService --> LedgerService : uses')
                elif '.r.> DataAccess_IF' in line:
                    new_lines.append('DepositService --> Database : uses')
                else:
                    new_lines.append(line)
            elif 'BonusService_IF' in line and '.r.> DataAccess_IF' in line:
                new_lines.append('BonusService --> Database : uses')
            elif 'LedgerService_IF' in line and '.r.> DataAccess_IF' in line:
                new_lines.append('LedgerService --> Database : uses')
            elif 'WebUI' in line and ('.r.>' in line or '-up-' in line):
                # Keep WebUI to BackendAPI connection
                if 'BackendAPI' in line:
                    new_lines.append('WebUI --> BackendAPI : REST API / WebSocket')
                else:
                    continue
            else:
                new_lines.append(line)
    
    # Strategy 3: Remove packages, use simpler layout
    elif iteration == 3:
        # Keep packages but use hidden connections to force better layout
        for line in lines:
            if 'interface "' in line and 'as ' in line:
                continue
            if re.search(r'-\s*(up|down|left|right)\s*-', line):
                continue
            if re.search(r'\.(r|l|u|d)\.>', line):
                continue
            new_lines.append(line)
        # Add hidden connections to force vertical layout
        new_lines.append('')
        new_lines.append("' Force vertical layout")
        new_lines.append('WebUI -[hidden]down-> BackendAPI')
        new_lines.append('BackendAPI -[hidden]down-> PrintService')
        new_lines.append('PrintService -[hidden]down-> PricingService')
        new_lines.append('PricingService -[hidden]down-> PaymentService')
        new_lines.append('PaymentService -[hidden]down-> RefundService')
        new_lines.append('RefundService -[hidden]down-> DepositService')
        new_lines.append('DepositService -[hidden]down-> BonusService')
        new_lines.append('BonusService -[hidden]down-> LedgerService')
        new_lines.append('LedgerService -[hidden]down-> PrinterController')
        new_lines.append('PrinterController -[hidden]down-> FileStorage')
        new_lines.append('FileStorage -[hidden]down-> PaymentGateway')
        new_lines.append('PaymentGateway -[hidden]down-> Database')
    
    # Strategy 4: Use top to bottom with hidden horizontal layout for Business Services
    elif iteration == 4:
        # Change to top to bottom
        for line in lines:
            if re.match(r'^\s*(top to bottom|left to right)\s+direction', line):
                new_lines.append('top to bottom direction')
            elif 'interface "' in line and 'as ' in line:
                continue
            elif re.search(r'-\s*(up|down|left|right)\s*-', line):
                continue
            elif re.search(r'\.(r|l|u|d)\.>', line):
                continue
            else:
                new_lines.append(line)
        # Add hidden horizontal layout for Business Services
        new_lines.append('')
        new_lines.append("' Force horizontal layout for Business Services")
        new_lines.append('PrintService -[hidden]right-> PricingService')
        new_lines.append('PricingService -[hidden]right-> PaymentService')
        new_lines.append('PaymentService -[hidden]right-> RefundService')
        new_lines.append('RefundService -[hidden]right-> DepositService')
        new_lines.append('DepositService -[hidden]right-> BonusService')
        new_lines.append('BonusService -[hidden]right-> LedgerService')
    
    # Strategy 5: Last resort - minimal connections
    else:
        # Keep only essential connections, remove all interfaces
        for line in lines:
            if 'interface "' in line:
                continue
            if re.search(r'-\s*(up|down|left|right)\s*-', line):
                continue
            if re.search(r'\.(r|l|u|d)\.>', line):
                continue
            if line.strip().startswith("'") and ('Frontend to API' in line or 'API Gateway to' in line or 'Business Services' in line):
                continue
            new_lines.append(line)
        # Add minimal direct connections
        new_lines.append('')
        new_lines.append("' Essential connections only")
        new_lines.append('WebUI --> BackendAPI')
        new_lines.append('BackendAPI --> PrintService')
        new_lines.append('BackendAPI --> PricingService')
        new_lines.append('BackendAPI --> PaymentService')
        new_lines.append('BackendAPI --> RefundService')
        new_lines.append('BackendAPI --> DepositService')
        new_lines.append('BackendAPI --> BonusService')
        new_lines.append('BackendAPI --> LedgerService')
        new_lines.append('PrintService --> PricingService')
        new_lines.append('PrintService --> PaymentService')
        new_lines.append('PrintService --> PrinterController')
        new_lines.append('PrintService --> FileStorage')
        new_lines.append('PrintService --> Database')
        new_lines.append('PricingService --> Database')
        new_lines.append('PaymentService --> LedgerService')
        new_lines.append('PaymentService --> PaymentGateway')
        new_lines.append('PaymentService --> Database')
        new_lines.append('RefundService --> PaymentService')
        new_lines.append('RefundService --> LedgerService')
        new_lines.append('RefundService --> Database')
        new_lines.append('DepositService --> BonusService')
        new_lines.append('DepositService --> PaymentGateway')
        new_lines.append('DepositService --> LedgerService')
        new_lines.append('DepositService --> Database')
        new_lines.append('BonusService --> Database')
        new_lines.append('LedgerService --> Database')
    
    return '\n'.join(new_lines)


def fix_diagram_dimensions(puml_file: Path, png_file: Path):
    """Fix diagram dimensions by iteratively adjusting PlantUML code."""
    print(f"\n🔧 Fixing diagram dimensions: {puml_file.name}")
    print(f"   Target: width <= {MAX_WIDTH}px, height <= {MAX_HEIGHT}px")
    
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n   Attempt {iteration}/{MAX_ITERATIONS}:")
        
        # Read current PlantUML content
        puml_content = read_puml_file(puml_file)
        
        # Apply fix strategy
        if iteration > 1:
            puml_content = fix_diagram_layout(puml_content, iteration)
            write_puml_file(puml_file, puml_content)
            print(f"   📝 Applied fix strategy {iteration}")
        
        # Render diagram
        print(f"   🎨 Rendering...")
        image_data = render_with_kroki(puml_content)
        
        if not image_data:
            print(f"   ❌ Failed to render")
            continue
        
        # Check dimensions
        width, height = get_image_dimensions(image_data)
        print(f"   📏 Dimensions: {width}x{height}px")
        
        # Save image
        with open(png_file, 'wb') as f:
            f.write(image_data)
        print(f"   💾 Saved: {png_file.name}")
        
        # Check if dimensions are acceptable
        if width <= MAX_WIDTH and height <= MAX_HEIGHT:
            print(f"   ✅ SUCCESS! Dimensions are acceptable")
            return True
        else:
            issues = []
            if width > MAX_WIDTH:
                issues.append(f"width {width}px > {MAX_WIDTH}px")
            if height > MAX_HEIGHT:
                issues.append(f"height {height}px > {MAX_HEIGHT}px")
            print(f"   ⚠️  Issues: {', '.join(issues)}")
            if iteration < MAX_ITERATIONS:
                print(f"   🔄 Trying different layout...")
    
    print(f"   ❌ Failed to fix after {MAX_ITERATIONS} attempts")
    return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_diagram_dimensions.py <puml_file> [png_file]")
        print("Example: python fix_diagram_dimensions.py component_diagrams/print_management_component_diagram.puml")
        sys.exit(1)
    
    puml_file = Path(sys.argv[1])
    if not puml_file.is_absolute():
        puml_file = BASE_DIR / puml_file
    
    if not puml_file.exists():
        print(f"❌ File not found: {puml_file}")
        sys.exit(1)
    
    # Determine PNG file path
    if len(sys.argv) >= 3:
        png_file = Path(sys.argv[2])
        if not png_file.is_absolute():
            png_file = BASE_DIR / png_file
    else:
        # Default: same name but .png extension
        png_file = puml_file.with_suffix('.png')
    
    success = fix_diagram_dimensions(puml_file, png_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

