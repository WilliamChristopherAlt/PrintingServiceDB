# Hướng Dẫn Hiển Thị Sơ Đồ Tầng Cho Máy In

## Tổng Quan

- **Input**: Có `printer_id` của một máy in
- **Database**: `floor.file_url` chứa URL Supabase đến ảnh PNG sơ đồ tầng
- **Database**: `printer_physical.printer_pixel_coordinate` chứa JSON với tọa độ pixel của máy in
- **Backend**: API nhận `printer_id`, trả về `diagram_url` và thông tin máy in đó kèm `pixel_coordinate`
- **Frontend**: Load ảnh từ URL, render icon máy in tại tọa độ pixel

---

## 1. Database Schema

### Bảng `floor`
```sql
file_url VARCHAR(500) NULL  -- URL Supabase đến ảnh PNG sơ đồ
```
**Ví dụ**: `https://abc123.supabase.co/storage/v1/object/public/floor_diagrams/LIBRARY_F1.png`

### Bảng `printer_physical`
```sql
printer_pixel_coordinate VARCHAR(100) NULL  -- JSON: {"grid": [x, y], "pixel": [x, y]}
```
**Ví dụ**: `{"grid": [12.5, 8.2], "pixel": [1200, 820]}`

**Lưu ý**: 
- Dùng `pixel` array cho frontend (tọa độ pixel trên ảnh)
- `grid` chỉ để tham khảo/debug

---

## 2. Backend API

### Endpoint
```
GET /api/printers/{printer_id}/floor-diagram
```

### Response Format
```json
{
  "printer": {
    "printer_id": "uuid",
    "serial_number": "HP-001",
    "room_name": "Computer Lab 1",
    "room_code": "101",
    "floor_number": 1,
    "building_code": "LIBRARY",
    "building_name": "Library & Research Center",
    "status": "idle",
    "is_enabled": true,
    "pixel_coordinate": {
      "pixel": [1200, 820]  // [x, y] - tọa độ pixel trên ảnh
    }
  },
  "floor": {
    "floor_id": "uuid",
    "floor_number": 1,
    "diagram_url": "https://...supabase.co/.../LIBRARY_F1.png"
  }
}
```

### SQL Query
```sql
SELECT 
    pp.printer_id,
    pp.serial_number,
    pp.status,
    pp.is_enabled,
    pp.printer_pixel_coordinate,  -- Parse JSON này thành object
    r.room_id,
    r.room_code,
    r.room_name,
    f.floor_id,
    f.floor_number,
    f.file_url AS diagram_url,
    b.building_code,
    b.campus_name AS building_name
FROM printer_physical pp
INNER JOIN room r ON pp.room_id = r.room_id
INNER JOIN floor f ON r.floor_id = f.floor_id
INNER JOIN building b ON f.building_id = b.building_id
WHERE pp.printer_id = @printer_id;
```

### Xử Lý Backend

1. **Query**: Join từ `printer_physical` -> `room` -> `floor` -> `building` để lấy đầy đủ thông tin
2. **Parse JSON**: Parse `printer_pixel_coordinate` từ string thành object
3. **Validate**: Kiểm tra máy in có tồn tại và có `pixel_coordinate` không
4. **Format**: Trả về `pixel_coordinate` dưới dạng object, không phải string

**Code Example (C#/Python/Node.js):**
```javascript
// Parse printer_pixel_coordinate
if (result.printer_pixel_coordinate) {
  result.pixel_coordinate = JSON.parse(result.printer_pixel_coordinate);
} else {
  result.pixel_coordinate = null;
}

// Response structure
const response = {
  printer: {
    printer_id: result.printer_id,
    serial_number: result.serial_number,
    room_name: result.room_name,
    room_code: result.room_code,
    floor_number: result.floor_number,
    building_code: result.building_code,
    building_name: result.building_name,
    status: result.status,
    is_enabled: result.is_enabled,
    pixel_coordinate: result.pixel_coordinate
  },
  floor: {
    floor_id: result.floor_id,
    floor_number: result.floor_number,
    diagram_url: result.diagram_url
  }
};
```

---

## 3. Frontend Implementation

### Bước 1: Load Ảnh Sơ Đồ

```javascript
// Fetch data từ API với printer_id
const printerId = 'your-printer-id';
const response = await fetch(`/api/printers/${printerId}/floor-diagram`);
const data = await response.json();

// Load ảnh
const diagramImage = new Image();
diagramImage.src = data.floor.diagram_url;
diagramImage.onload = () => {
  renderPrinter(data.printer, diagramImage);
};
```

### Bước 2: HTML Structure

```html
<div class="floor-diagram-container">
  <div class="diagram-wrapper" style="position: relative;">
    <img id="floor-diagram" src="" alt="Floor Diagram" />
    <svg id="printer-overlay" 
         style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
    </svg>
  </div>
</div>
```

### Bước 3: Render Printer Icon

```javascript
function renderPrinter(printer, diagramImage) {
  const overlay = document.getElementById('printer-overlay');
  const diagram = document.getElementById('floor-diagram');
  
  // Set SVG dimensions = image dimensions
  const imageWidth = diagramImage.width;
  const imageHeight = diagramImage.height;
  overlay.setAttribute('viewBox', `0 0 ${imageWidth} ${imageHeight}`);
  overlay.setAttribute('width', imageWidth);
  overlay.setAttribute('height', imageHeight);
  
  overlay.innerHTML = '';
  
  // Kiểm tra có tọa độ không
  if (!printer.pixel_coordinate || !printer.pixel_coordinate.pixel) {
    console.warn('Printer không có tọa độ pixel');
    return;
  }
  
  const [pixelX, pixelY] = printer.pixel_coordinate.pixel;
  
  // Tạo icon máy in (50x50px, center tại pixelX, pixelY)
  const iconSize = 50;
  const iconX = pixelX - iconSize / 2;
  const iconY = pixelY - iconSize / 2;
  
  // Tạo SVG group
  const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  group.setAttribute('data-printer-id', printer.printer_id);
  group.style.cursor = 'pointer';
  group.style.pointerEvents = 'all';
  
  // Background rectangle
  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('x', iconX);
  bg.setAttribute('y', iconY);
  bg.setAttribute('width', iconSize);
  bg.setAttribute('height', iconSize);
  bg.setAttribute('fill', getPrinterColor(printer.status));
  bg.setAttribute('stroke', '#FFF');
  bg.setAttribute('stroke-width', '3');
  bg.setAttribute('rx', '5');
  
  // Printer icon (đơn giản)
  const icon = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  icon.setAttribute('cx', pixelX);
  icon.setAttribute('cy', pixelY);
  icon.setAttribute('r', '15');
  icon.setAttribute('fill', '#FFF');
  
  // Label
  const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  label.setAttribute('x', pixelX);
  label.setAttribute('y', pixelY + iconSize / 2 + 15);
  label.setAttribute('text-anchor', 'middle');
  label.setAttribute('font-size', '14');
  label.setAttribute('font-weight', 'bold');
  label.setAttribute('fill', '#000');
  label.textContent = printer.serial_number;
  
  // Assemble
  group.appendChild(bg);
  group.appendChild(icon);
  group.appendChild(label);
  
  // Click handler (optional)
  group.addEventListener('click', () => {
    showPrinterDetails(printer);
  });
  
  // Tooltip
  group.setAttribute('title', `${printer.serial_number} - ${printer.room_name}`);
  
  overlay.appendChild(group);
}

function getPrinterColor(status) {
  const colors = {
    'idle': '#2C3E50',
    'printing': '#27AE60',
    'maintained': '#E67E22',
    'unplugged': '#95A5A6'
  };
  return colors[status] || '#2C3E50';
}
```

### Bước 4: Handle Responsive (Nếu ảnh bị scale)

```javascript
function updateOverlayScale() {
  const diagram = document.getElementById('floor-diagram');
  const overlay = document.getElementById('printer-overlay');
  
  const imageRect = diagram.getBoundingClientRect();
  const naturalWidth = diagram.naturalWidth;
  const naturalHeight = diagram.naturalHeight;
  
  // Scale SVG overlay theo tỷ lệ ảnh đã bị resize
  const scaleX = imageRect.width / naturalWidth;
  const scaleY = imageRect.height / naturalHeight;
  
  overlay.style.width = `${imageRect.width}px`;
  overlay.style.height = `${imageRect.height}px`;
  overlay.style.transform = `scale(${scaleX}, ${scaleY})`;
  overlay.style.transformOrigin = 'top left';
}

window.addEventListener('resize', updateOverlayScale);
diagramImage.onload = () => {
  updateOverlayScale();
};
```

---

## 4. Tọa Độ Pixel

- **Origin**: Góc trên-trái của ảnh = (0, 0)
- **X-axis**: Tăng từ trái sang phải
- **Y-axis**: Tăng từ trên xuống dưới
- **Đơn vị**: Pixel (khớp với kích thước ảnh PNG)

**Ví dụ**: `"pixel": [1200, 820]` nghĩa là:
- X = 1200px từ bên trái
- Y = 820px từ trên xuống

---

## 5. Lưu Ý Quan Trọng

### Backend
- ✅ Query từ `printer_id` -> join đến `room` -> `floor` để lấy `diagram_url`
- ✅ Parse `printer_pixel_coordinate` JSON string thành object trước khi trả về
- ✅ Trả về cả thông tin máy in và floor trong response
- ✅ Trả về `pixel_coordinate.pixel` array để FE dùng

### Frontend
- ✅ Nhận `printer_id` làm input, gọi API để lấy floor diagram
- ✅ Kiểm tra `pixel_coordinate` tồn tại trước khi render
- ✅ Set SVG `viewBox` và dimensions = kích thước ảnh thực tế
- ✅ Nếu ảnh bị resize, scale SVG overlay tương ứng
- ✅ Handle trường hợp máy in không có tọa độ (hiển thị thông báo)

### Lỗi Thường Gặp
1. **Icon không hiện**: Kiểm tra `pixel_coordinate` có null không
2. **Icon sai vị trí**: Kiểm tra SVG dimensions có khớp với ảnh không
3. **Ảnh không load**: Kiểm tra CORS và public access của Supabase bucket

---

## 6. Example Response

```json
{
  "printer": {
    "printer_id": "p1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "serial_number": "HP-LIB-001",
    "room_name": "Computer Lab 1",
    "room_code": "101",
    "floor_number": 1,
    "building_code": "LIBRARY",
    "building_name": "Library & Research Center",
    "status": "idle",
    "is_enabled": true,
    "pixel_coordinate": {
      "pixel": [1200, 820]
    }
  },
  "floor": {
    "floor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "floor_number": 1,
    "diagram_url": "https://abc123.supabase.co/storage/v1/object/public/floor_diagrams/LIBRARY_F1.png"
  }
}
```

---

## Tóm Tắt

1. **Input**: Có `printer_id` của máy in cần hiển thị
2. **BE**: Query từ `printer_id` -> join `room` -> `floor` để lấy `diagram_url` và `pixel_coordinate`, parse JSON, trả về API
3. **FE**: Load ảnh từ `diagram_url`, tạo SVG overlay, render icon máy in tại `pixel_coordinate.pixel`
4. **Tọa độ**: Pixel coordinates là vị trí tuyệt đối trên ảnh (góc trên-trái = 0,0)

