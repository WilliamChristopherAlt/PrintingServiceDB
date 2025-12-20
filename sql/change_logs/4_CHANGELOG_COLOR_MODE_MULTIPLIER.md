# NHẬT KÝ THAY ĐỔI: COLOR_MODE_PRICE - CHUYỂN TỪ PRICE_PER_PAGE SANG PRICE_MULTIPLIER
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN
Thay đổi cấu trúc bảng `color_mode_price` từ lưu giá tuyệt đối (`price_per_page`) sang lưu hệ số nhân (`price_multiplier`) áp dụng lên giá cơ bản của kích thước trang.

---

## THAY ĐỔI CHI TIẾT

### BẢNG `color_mode_price` - THAY ĐỔI CỘT

#### Thay đổi:
- **THAY ĐỔI cột:** `price_per_page` (DECIMAL(10,4)) → `price_multiplier` (DECIMAL(5,4))
  - **Trước:** `price_per_page DECIMAL(10, 4) NOT NULL CHECK (price_per_page >= 0)`
  - **Sau:** `price_multiplier DECIMAL(5, 4) NOT NULL CHECK (price_multiplier >= 0)`

#### Lý do:
**Trước đây:**
- `color_mode_price.price_per_page` lưu giá tuyệt đối mỗi trang, không phụ thuộc vào kích thước trang
- Ví dụ: black-white = $0.10/trang, color = $0.30/trang (giống nhau cho mọi kích thước)
- Công thức: `subtotal = total_pages × color_mode_price.price_per_page`

**Sau khi thay đổi:**
- `color_mode_price.price_multiplier` lưu hệ số nhân áp dụng lên `page_size_price.page_price`
- Ví dụ: black-white = 0.5x, grayscale = 0.75x, color = 1.5x
- Công thức: `subtotal = total_pages × page_size_price.page_price × color_mode_price.price_multiplier`
- Với A4 = $0.20: black-white = $0.10, grayscale = $0.15, color = $0.30
- Với A3 = $0.40: black-white = $0.20, grayscale = $0.30, color = $0.60

**Lợi ích:**
1. **Linh hoạt hơn:** Giá tự động thay đổi theo kích thước trang
2. **Nhất quán:** Cùng một hệ số áp dụng cho mọi kích thước, dễ hiểu và quản lý
3. **Dễ quản lý:** Chỉ cần thay đổi `page_size_price` để ảnh hưởng toàn bộ hệ thống
4. **Logic rõ ràng:** Giá = (giá cơ bản) × (hệ số màu), phản ánh đúng cách tính giá thực tế

---

### VIEW `print_job_pricing` - CẬP NHẬT

#### Thay đổi:
- **THAY ĐỔI cột:** `cmp.price_per_page AS color_mode_price_per_page` → `cmp.price_multiplier AS color_mode_price_multiplier`

#### Lý do:
Đồng bộ với thay đổi trong bảng `color_mode_price`.

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi tạo print_job mới:
- **Công thức tính giá mới:**
  ```sql
  price_per_page = page_size_price.page_price × color_mode_price.price_multiplier
  subtotal_before_discount = total_pages × price_per_page
  ```
- Phải lấy cả `page_size_price.page_price` và `color_mode_price.price_multiplier` để tính giá
- Không còn dùng trực tiếp `color_mode_price.price_per_page`

### Khi truy vấn giá:
- View `print_job_pricing` trả về `color_mode_price_multiplier` thay vì `color_mode_price_per_page`
- Ứng dụng cần nhân `base_price_per_page × color_mode_price_multiplier` để có giá cuối cùng

### Migration:
- Cần migrate dữ liệu cũ từ `price_per_page` sang `price_multiplier`
- Công thức chuyển đổi: `price_multiplier = price_per_page / base_page_price` (với base_page_price là giá A4 mặc định)
- Hoặc tính lại dựa trên giá trị mong muốn cho từng chế độ màu

---

## GIÁ TRỊ MẶC ĐỊNH

Sau khi thay đổi, các giá trị mặc định:
- **black-white:** `price_multiplier = 0.5` (50% giá cơ bản - rẻ nhất)
- **grayscale:** `price_multiplier = 0.75` (75% giá cơ bản)
- **color:** `price_multiplier = 1.5` (150% giá cơ bản - đắt nhất)

Với `page_size_price.page_price` mặc định:
- A4 = $0.20 → black-white = $0.10, grayscale = $0.15, color = $0.30
- A3 = $0.40 → black-white = $0.20, grayscale = $0.30, color = $0.60
- A5 = $0.10 → black-white = $0.05, grayscale = $0.075, color = $0.15

---

## NGÀY THỰC HIỆN
Thay đổi được thực hiện: 2025-12-19

---

## GHI CHÚ
- File `design.sql` đã được cập nhật với cấu trúc mới
- Script `generate.py` đã được cập nhật để sử dụng `price_multiplier`
- View `print_job_pricing` đã được cập nhật
- File `DEVELOPER_GUIDE.md` đã được cập nhật với công thức mới
- File `balance_notes.txt` đã được cập nhật với hệ số mới
- Diagram `db_diagram.puml` đã được cập nhật

