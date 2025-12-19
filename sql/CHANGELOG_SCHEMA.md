# NHẬT KÝ THAY ĐỔI SCHEMA CƠ SỞ DỮ LIỆU
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN
Tài liệu này ghi lại các thay đổi về schema cơ sở dữ liệu được thực hiện để cải thiện cấu trúc dữ liệu và đảm bảo tính nhất quán.

---

## CÁC THAY ĐỔI CHI TIẾT

### 1. TẠO BẢNG `color_mode` MỚI

#### Thay đổi:
- **THÊM bảng:** `color_mode`
- **Các cột:**
  - `color_mode_id` (UNIQUEIDENTIFIER, PK)
  - `color_mode_name` (VARCHAR(50), UNIQUE) - Tên chế độ màu: 'color', 'grayscale', 'black-white'
  - `description` (TEXT)
  - `created_at` (DATETIME)

#### Lý do:
Tách riêng định nghĩa chế độ màu khỏi giá cả, tương tự như cách `page_size` và `page_size_price` được tách riêng. Điều này cho phép:
- Một chế độ màu có thể có nhiều cấu hình giá khác nhau theo thời gian
- Quản lý danh sách chế độ màu độc lập với giá cả
- Nhất quán với cấu trúc `page_size` / `page_size_price`

---

### 2. BẢNG `color_mode_price` - THAY ĐỔI CẤU TRÚC

#### Thay đổi:
- **XÓA cột:** `color_mode_name` (VARCHAR(50))
- **THÊM cột:** `color_mode_id` (UNIQUEIDENTIFIER, FK → `color_mode.color_mode_id`)
- **THÊM foreign key:** `FOREIGN KEY (color_mode_id) REFERENCES color_mode(color_mode_id)`

#### Lý do:
Thay vì lưu tên chế độ màu trực tiếp trong bảng giá, tham chiếu đến bảng `color_mode`. Cách này:
- Tách biệt định nghĩa chế độ màu và giá cả
- Cho phép một chế độ màu có nhiều bản ghi giá theo thời gian
- Nhất quán với mô hình `page_size` / `page_size_price`

---

### 3. BẢNG `print_job` - THAY ĐỔI CẤU TRÚC

#### Các cột được THÊM:
1. **`page_size_price_id`** (UNIQUEIDENTIFIER, NOT NULL)
   - FK → `page_size_price(price_id)`
   - Lưu cấu hình giá kích thước trang được dùng khi tạo job
   - **Lý do:** Khi giá thay đổi sau này, vẫn biết chính xác giá nào đã áp dụng cho job này

2. **`color_mode_price_id`** (UNIQUEIDENTIFIER, NOT NULL)
   - FK → `color_mode_price(setting_id)`
   - Lưu cấu hình giá chế độ màu được dùng khi tạo job
   - **Lý do:** Tương tự `page_size_price_id`, đảm bảo tính lịch sử. Tham chiếu đến `color_mode_price` thay vì chỉ `color_mode` vì `color_mode_price` mã hóa đồng thời cả chế độ màu và giá tại thời điểm đó

3. **`page_discount_package_id`** (UNIQUEIDENTIFIER, NULL)
   - FK → `page_discount_package(package_id)`
   - Lưu gói giảm giá khối lượng được áp dụng (nếu có)
   - **Lý do:** Ghi lại gói giảm giá nào đã được áp dụng để kiểm tra và audit

4. **`total_pages`** (INT, NOT NULL)
   - Tổng số trang (từ `print_job_page`)
   - **Lý do:** Lưu để tránh phải đếm lại từ `print_job_page` mỗi lần truy vấn, cải thiện hiệu suất

5. **`subtotal_before_discount`** (DECIMAL(10,2), NOT NULL)
   - Tổng tiền trước giảm giá
   - **Lý do:** Lưu giá trị đã tính để tránh tính lại, đảm bảo giá trị không thay đổi nếu logic tính toán thay đổi sau này

6. **`discount_percentage`** (DECIMAL(5,4), NULL)
   - Phần trăm giảm giá từ `page_discount_package`
   - **Lý do:** Lưu giá trị tại thời điểm tạo job để đảm bảo tính lịch sử, vì `page_discount_package.discount_percentage` có thể thay đổi

7. **`discount_amount`** (DECIMAL(10,2), NOT NULL)
   - Số tiền giảm giá đã tính
   - **Lý do:** Lưu giá trị đã tính để tránh tính lại và đảm bảo tính nhất quán

8. **`total_price`** (DECIMAL(10,2), NOT NULL)
   - Tổng tiền cuối cùng sau giảm giá
   - **Lý do:** Lưu giá trị cuối cùng để truy vấn nhanh mà không cần tính toán

#### Các cột bị XÓA:
1. **`paper_size_id`** (UNIQUEIDENTIFIER)
   - **Lý do:** Thừa vì có thể lấy từ `page_size_price.page_size_id` thông qua `page_size_price_id`

2. **`color_mode`** (VARCHAR(20))
   - **Lý do:** Thay bằng `color_mode_price_id` để tham chiếu đến cấu hình giá, mã hóa đồng thời cả chế độ màu và giá

#### Foreign keys được THÊM:
- `FOREIGN KEY (page_size_price_id) REFERENCES page_size_price(price_id)`
- `FOREIGN KEY (color_mode_price_id) REFERENCES color_mode_price(setting_id)`
- `FOREIGN KEY (page_discount_package_id) REFERENCES page_discount_package(package_id)`

#### Foreign key bị XÓA:
- `FOREIGN KEY (paper_size_id) REFERENCES page_size(page_size_id)` - không cần vì có thể lấy qua `page_size_price`

---

### 4. VIEW `print_job_pricing` - CẬP NHẬT

#### Thay đổi:
- Thay đổi từ tính toán các trường giá sang đọc trực tiếp từ các cột đã lưu trong `print_job`
- Thêm JOIN với `color_mode` để lấy `color_mode_name`

#### Lý do:
Các trường giá đã được lưu trong `print_job`, view chỉ cần đọc và JOIN với các bảng tham chiếu để lấy thông tin bổ sung.

---

### 5. VIEW `student_printing_history` - CẬP NHẬT

#### Thay đổi:
- Thay đổi JOIN từ `page_size` trực tiếp sang JOIN qua `page_size_price` để lấy `page_size`
- Thêm JOIN với `color_mode` để lấy `color_mode_name`

#### Lý do:
Đồng bộ với cấu trúc mới: `print_job` không còn `paper_size_id` trực tiếp, phải lấy qua `page_size_price`.

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi tạo print_job mới:
- Phải cung cấp `page_size_price_id` và `color_mode_price_id` thay vì chỉ `paper_size_id` và `color_mode` (string)
- Phải tính và lưu các trường: `total_pages`, `subtotal_before_discount`, `discount_percentage`, `discount_amount`, `total_price`
- Phải xác định `page_discount_package_id` dựa trên tổng số trang

### Khi truy vấn giá:
- Có thể đọc trực tiếp từ `print_job.total_price` hoặc các trường giá khác
- Có thể sử dụng view `print_job_pricing` để lấy thông tin đầy đủ

---

## NGÀY THỰC HIỆN
Các thay đổi được thực hiện trong phiên làm việc này.

---

## GHI CHÚ
- Tất cả các thay đổi đã được cập nhật trong file `design.sql`
- Script sinh dữ liệu (`generate.py`) cần được cập nhật để phù hợp với schema mới
- Các diagram module đã được tái tạo với cấu trúc mới
- Tất cả các view đã được cập nhật để hoạt động với schema mới
