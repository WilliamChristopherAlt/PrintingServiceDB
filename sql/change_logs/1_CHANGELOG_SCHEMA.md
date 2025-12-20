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

**Lưu ý:** Thay đổi từ `price_per_page` sang `price_multiplier` được ghi lại trong file riêng: `CHANGELOG_COLOR_MODE_MULTIPLIER.md`

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

### 6. BẢNG `refund_print_job` VÀ VIEW `student_balance_view` - CẬP NHẬT

#### Thay đổi:
- **THÊM bảng:** `refund_print_job`
- **Các cột:**
  - `refund_id` (UNIQUEIDENTIFIER, PK)
  - `job_id` (UNIQUEIDENTIFIER, UNIQUE, FK → `print_job.job_id`)
  - `pages_not_printed` (INT, NOT NULL, ≥ 0) – số trang **chưa in** tại thời điểm hủy job
  - `created_at` (DATETIME)
- **THÊM index:** `idx_refund_job` trên `job_id`

- **CẬP NHẬT view `student_balance_view`:**
  - Thêm một thành phần cộng vào số dư:
    \[
      \text{refund\_amount} = \sum\limits_{\text{refund\_print\_job}} \bigl( \text{print\_job.total\_price} \times \frac{\text{pages\_not\_printed}}{\text{total\_pages}} \bigr)
    \]
  - Cụ thể trong SQL:
    ```sql
    + COALESCE((
        SELECT SUM(
            pj.total_price * (CAST(r.pages_not_printed AS DECIMAL(10,4)) / NULLIF(pj.total_pages, 0))
        )
        FROM refund_print_job r
        JOIN print_job pj ON r.job_id = pj.job_id
        WHERE pj.student_id = s.student_id
    ), 0)
    ```

#### Lý do:
- Khi hủy một print job chưa in hết, chỉ phần trang **chưa in** mới được hoàn tiền.
- `refund_print_job` lưu lại:
  - Job nào đã được hoàn tiền
  - Bao nhiêu trang chưa in tại thời điểm hủy
- `student_balance_view` dùng `print_job.total_price` và tỷ lệ `pages_not_printed / total_pages` để tính số tiền hoàn lại, nên:
  - Không cần trường số dư trong bảng
  - Có thể thay đổi logic hoàn tiền trong view mà không đụng tới dữ liệu gốc
  - Rõ ràng, kiểm tra được: nhìn vào `refund_print_job` là biết job nào đã được refund và ở mức nào

---

### 7. BẢNG `uploaded_file` VÀ BẢNG `print_job` - TÁCH THÔNG TIN FILE

#### Thay đổi:
- **THÊM bảng:** `uploaded_file`
- **Các cột:**
  - `uploaded_file_id` (UNIQUEIDENTIFIER, PK)
  - `student_id` (UNIQUEIDENTIFIER, FK → `student.student_id`)
  - `file_name` (VARCHAR(500)) – tên file gốc
  - `file_type` (VARCHAR(10)) – đuôi file: pdf, docx, webp, ...
  - `file_size_kb` (INT) – dung lượng file (KB)
  - `file_url` (VARCHAR(500)) – URL tới file trên storage (Supabase, S3, ...)
  - `created_at` (DATETIME)
- **THÊM foreign key:** `FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE`

- **CẬP NHẬT bảng `print_job`:**
  - **XÓA cột:**
    - `file_url` (VARCHAR(500))
    - `file_type` (VARCHAR(10))
    - `file_size_kb` (INT)
  - **THÊM cột:**
    - `uploaded_file_id` (UNIQUEIDENTIFIER, NOT NULL, FK → `uploaded_file.uploaded_file_id`)

- **CẬP NHẬT view `student_printing_history`:**
  - Thay vì lấy trực tiếp `pj.file_url`, view JOIN thêm `uploaded_file`:
    - Chọn: `uf.file_name`, `uf.file_type`, `uf.file_url`
  - Cập nhật phần `GROUP BY` tương ứng (dùng cột của `uploaded_file` thay cho `pj.file_url`)

#### Lý do:
- Giao diện web có hai bước rõ ràng:
  1. **Upload / Save file** (chỉ lưu file, chưa in)
  2. **Tạo lệnh in** từ file đã upload (tạo `print_job`)
- Tách bảng `uploaded_file`:
  - Cho phép sinh viên lưu trữ file như một “thư mục tài liệu” riêng
  - Một file có thể được in nhiều lần (nhiều `print_job` cùng tham chiếu đến một `uploaded_file`)
  - `print_job` chỉ tập trung vào cấu hình in, trạng thái in và pricing, không ôm thêm thông tin file

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi tạo print_job mới:
- Phải cung cấp `uploaded_file_id` (thay vì truyền trực tiếp file_url / file_type / file_size_kb)
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
