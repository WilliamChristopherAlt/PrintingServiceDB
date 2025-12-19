# HƯỚNG DẪN PHÁT TRIỂN
## Smart Printing Service System (SSPS) - Database Schema Guide

---

## MỤC LỤC CÁC MODULE

### 1. Quản lý Người dùng & Xác thực
**Bảng:** `user`, `student`, `staff`, `refresh_token`, `password_reset_token`

### 2. Cơ cấu Học thuật
**Bảng:** `faculty`, `department`, `major`, `class`, `academic_year`, `semester`

### 3. Quản lý Tòa nhà & Vị trí
**Bảng:** `building`, `floor`, `room`

### 4. Quản lý Máy in
**Bảng:** `brand`, `printer_model`, `printer_physical`, `page_size`

### 5. Quản lý Công việc In
**Bảng:** `uploaded_file`, `print_job`, `print_job_page`, `student`, `printer_physical`, `page_size`, `page_size_price`

### 6. Quản lý Thanh toán & Số dư
**Bảng:** `deposit`, `deposit_bonus_package`, `payment`, `semester_bonus`, `student_semester_bonus`, `student`, `print_job`, `refund_print_job`, `student_wallet_ledger`

### 7. Cấu hình Giá
**Bảng:** `color_mode`, `color_mode_price`, `page_size_price`, `page_discount_package`, `page_size`, `print_job`

### 8. Mua giấy & Quản lý Kho
**Bảng:** `fund_source`, `supplier_paper_purchase`, `paper_purchase_item`, `page_size`, `staff`

### 9. Cấu hình Hệ thống
**Bảng:** `system_configuration`, `permitted_file_type`, `staff`

### 10. Kiểm tra & Ghi nhật ký
**Bảng:** `printer_log`, `system_audit_log`, `user`, `printer_physical`, `print_job`

---

## GIẢI THÍCH CHI TIẾT CÁC MODULE

### 1. QUẢN LÝ NGƯỜI DÙNG & XÁC THỰC

**Mục đích:** Quản lý thông tin người dùng và xác thực hệ thống.

**Bảng chính:**
- `user`: Thông tin cơ bản của tất cả người dùng (email, password, profile, etc.)
- `student`: Thông tin sinh viên, liên kết với `user` và `class`
- `staff`: Thông tin nhân viên, liên kết với `user`
- `refresh_token`: Token làm mới để duy trì đăng nhập
- `password_reset_token`: Token để reset mật khẩu

**Cách hoạt động:**
- Tất cả người dùng (sinh viên và nhân viên) đều có record trong `user`
- `student` và `staff` là các bảng mở rộng, mỗi record tham chiếu đến một `user`
- Xác thực sử dụng `refresh_token` để quản lý session
- Reset mật khẩu sử dụng `password_reset_token` với thời gian hết hạn

---

### 2. CƠ CẤU HỌC THUẬT

**Mục đích:** Quản lý cấu trúc tổ chức học thuật của trường.

**Bảng chính:**
- `faculty`: Khoa (ví dụ: Computer Science & Engineering)
- `department`: Bộ môn thuộc khoa (ví dụ: Computer Science)
- `major`: Chuyên ngành thuộc bộ môn (ví dụ: Computer Science, Data Science)
- `class`: Lớp học thuộc chuyên ngành và năm học
- `academic_year`: Năm học (ví dụ: 2023-2024)
- `semester`: Học kỳ (Fall, Spring, Summer) thuộc năm học

**Cách hoạt động:**
- Cấu trúc phân cấp: Faculty → Department → Major → Class
- Mỗi `class` thuộc một `major` và một `academic_year`
- `semester` được tạo cho mỗi `academic_year` (Fall, Spring, Summer)
- Sinh viên được gán vào một `class` cụ thể

---

### 3. QUẢN LÝ TÒA NHÀ & VỊ TRÍ

**Mục đích:** Quản lý vị trí vật lý của các máy in trong khuôn viên.

**Bảng chính:**
- `building`: Tòa nhà (ví dụ: Library, Main Academy)
- `floor`: Tầng trong tòa nhà
- `room`: Phòng trên mỗi tầng

**Cách hoạt động:**
- Cấu trúc phân cấp: Building → Floor → Room
- Mỗi `room` thuộc một `floor`, mỗi `floor` thuộc một `building`
- Máy in được đặt trong các `room` cụ thể
- Hỗ trợ lưu trữ file diagram của floor (SVG/PNG) trong `floor.file_url`

---

### 4. QUẢN LÝ MÁY IN

**Mục đích:** Quản lý thông tin và trạng thái của các máy in vật lý.

**Bảng chính:**
- `brand`: Thương hiệu máy in (ví dụ: HP, Canon)
- `printer_model`: Model máy in, thuộc một brand
- `printer_physical`: Máy in vật lý cụ thể, thuộc một model và đặt trong một room
- `page_size`: Kích thước giấy hỗ trợ (A3, A4, A5)

**Cách hoạt động:**
- `printer_model` định nghĩa đặc tính kỹ thuật (hỗ trợ màu, duplex, tốc độ in, kích thước giấy tối đa)
- `printer_physical` là instance thực tế của một model, có serial number và trạng thái
- Trạng thái máy in: `unplugged`, `idle`, `printing`, `maintained`
- Printing status: `printing`, `paper_jam`, `out_of_paper`, `out_of_toner`, etc.
- Mỗi máy in có thể có tọa độ pixel trên floor diagram (`printer_pixel_coordinate`)

---

### 5. QUẢN LÝ CÔNG VIỆC IN

**Mục đích:** Quản lý các công việc in của sinh viên.

**Bảng chính:**
- `uploaded_file`: File mà sinh viên upload (lưu trữ lâu dài, có thể in nhiều lần)
- `print_job`: Công việc in chính (tham chiếu đến `uploaded_file`)
- `print_job_page`: Chi tiết từng trang trong công việc in
- `student`: Sinh viên thực hiện công việc
- `printer_physical`: Máy in được sử dụng
- `page_size`: Kích thước giấy
- `page_size_price`: Cấu hình giá cho kích thước giấy

**Luồng Uploaded Files vs Print Job:**

1. **Uploaded Files (Lưu file, chưa in):**
   - Khi sinh viên upload file ở màn hình “Uploaded Files” / “My Documents”:
     - Tạo record trong `uploaded_file`:
       - `student_id`
       - `file_name`, `file_type`, `file_size_kb`
       - `file_url` (đường dẫn Supabase / storage)
       - `created_at`
   - Chưa tạo `print_job`, chưa trừ tiền, chưa ảnh hưởng số dư.

2. **Tạo Print Job từ Uploaded File:**
   - Sinh viên chọn một record trong `uploaded_file` và cấu hình in:
     - Kích thước giấy (`page_size_price_id`)
     - Chế độ màu (`color_mode_price_id`)
     - Gói giảm giá khối lượng (nếu có) (`page_discount_package_id`)
     - Hướng giấy (`page_orientation`), in 1 mặt / 2 mặt (`print_side`), số bản (`number_of_copy`)
   - Hệ thống tạo record trong `print_job` với:
     - `uploaded_file_id`: Tham chiếu tới file đã upload
     - Các FK cấu hình giá: `page_size_price_id`, `color_mode_price_id`, `page_discount_package_id`
     - Các tùy chọn in: `page_orientation`, `print_side`, `number_of_copy`
   - Hệ thống đếm số trang từ file (hoặc từ metadata đã phân tích) và tạo records trong `print_job_page`
   - Tính giá và lưu vào `print_job`:
     - `total_pages`: Tổng số trang (từ `print_job_page` count × `number_of_copy`)
     - `subtotal_before_discount`: Tổng tiền trước giảm giá
     - `discount_percentage`: Phần trăm giảm giá (từ `page_discount_package`)
     - `discount_amount`: Số tiền giảm giá
     - `total_price`: Tổng tiền cuối cùng

**Trạng thái Print Job:**
- `queued`: Đang chờ trong hàng đợi
- `printing`: Đang in
- `completed`: Hoàn thành
- `failed`: Thất bại
- `cancelled`: Đã hủy

**Quan trọng:**
- Tất cả giá được lưu trong `print_job` để đảm bảo tính lịch sử. Khi giá thay đổi sau này, các công việc in cũ vẫn giữ nguyên giá đã áp dụng.
- `uploaded_file` cho phép tái sử dụng cùng một file cho nhiều `print_job` (ví dụ: in lại, in cho lớp khác) mà không cần re-upload.

---

### 6. QUẢN LÝ THANH TOÁN & SỐ DƯ

**Mục đích:** Quản lý số dư và thanh toán của sinh viên.

**Bảng chính:**
- `deposit`: Nạp tiền vào tài khoản
- `deposit_bonus_package`: Gói bonus khi nạp tiền (ví dụ: nạp $50 được 10% bonus)
- `payment`: Thanh toán cho print job
- `semester_bonus`: Bonus mỗi học kỳ
- `student_semester_bonus`: Tracking sinh viên nào đã nhận bonus học kỳ
- `student`: Sinh viên
- `print_job`: Công việc in được thanh toán
- `refund_print_job`: Hoàn tiền cho các print job bị hủy (chỉ phần trang chưa in)

**CÁCH TÍNH SỐ DƯ (QUAN TRỌNG):**

Số dư KHÔNG được lưu trực tiếp trong bảng. Thay vào đó, sử dụng VIEW `student_balance_view` để tính toán động:

```sql
Số dư = 
  (Tổng tiền nạp đã hoàn thành + Bonus từ nạp tiền) +
  (Tổng bonus học kỳ đã nhận) -
  (Tổng tiền đã thanh toán từ số dư) +
  (Tổng tiền được hoàn lại từ các job bị hủy)
```

**Chi tiết:**

1. **Nạp tiền (`deposit`):**
   - Sinh viên nạp tiền thực tế (USD) vào tài khoản
   - `deposit_amount`: Số tiền nạp thực tế
   - `bonus_amount`: Bonus nhận được (từ `deposit_bonus_package` nếu đủ điều kiện)
   - `total_credited`: Tổng tiền được cộng vào số dư (`deposit_amount + bonus_amount`)
   - Chỉ tính vào số dư khi `payment_status = 'completed'`

2. **Bonus học kỳ (`semester_bonus` + `student_semester_bonus`):**
   - Mỗi học kỳ có thể có một khoản bonus cho sinh viên
   - `semester_bonus`: Định nghĩa số tiền bonus cho học kỳ
   - `student_semester_bonus`: Tracking sinh viên nào đã nhận bonus
   - Chỉ tính vào số dư khi `received = 1`

3. **Thanh toán (`payment`):**
   - Mỗi print job có một payment record
   - `amount_paid_from_balance`: Thanh toán từ số dư trong app
   - `amount_paid_directly`: Thanh toán trực tiếp (thẻ, tiền mặt)
   - `total_amount`: Tổng thanh toán (`amount_paid_from_balance + amount_paid_directly`)
   - Chỉ trừ số dư khi `payment_status = 'completed'` và `amount_paid_from_balance > 0`

4. **Hoàn tiền khi hủy in (`refund_print_job` + `print_job`):**
   - Khi một print job bị hủy trong khi chưa in xong:
     - Hệ thống in (hoặc service backend) xác định số trang **chưa in**: `pages_not_printed`
     - Ghi một record trong `refund_print_job`:
       - `job_id` → print job bị hủy
       - `pages_not_printed`
   - Số tiền hoàn lại được tính trong `student_balance_view`:
     ```sql
     refund_amount = print_job.total_price 
                     * (pages_not_printed / total_pages)
     ```
   - View cộng tổng `refund_amount` cho tất cả job của sinh viên vào số dư
   - Kịch bản điển hình:
     - Job giá $10, total_pages = 100
     - In được 40 trang, còn 60 trang chưa in → `pages_not_printed = 60`
     - `refund_amount = 10 * (60 / 100) = $6`
     - Hệ thống hoàn $6 vào số dư, $4 vẫn được tính là đã chi

**Ví dụ tính số dư:**

Sinh viên A:
- Nạp $50 (completed) → +$50 vào số dư
- Nạp $100 với bonus 10% (completed) → +$110 vào số dư
- Nhận bonus học kỳ Fall $20 (received = 1) → +$20 vào số dư
- Thanh toán print job $5 từ số dư (completed) → -$5 từ số dư
- Thanh toán print job $10 trực tiếp (completed) → Không ảnh hưởng số dư

**Số dư cuối cùng = $50 + $110 + $20 - $5 = $175**

**Lưu ý quan trọng:**
- Luôn sử dụng VIEW `student_balance_view` để hiển thị số dư cho user
- KHÔNG lưu số dư trong bảng `student` (sẽ không nhất quán)
- Khi hiển thị số dư, query từ view này
- Khi kiểm tra đủ tiền để thanh toán, tính toán từ view hoặc tính trực tiếp từ các bảng

**Kiến trúc Ledger Pattern:**

Hệ thống sử dụng **kiến trúc Ledger** (sổ cái) để quản lý số dư:

1. **Bảng domain (giữ nguyên):**
   - `deposit`: Nạp tiền
   - `payment`: Thanh toán
   - `refund_print_job`: Hoàn tiền
   - `student_semester_bonus`: Bonus học kỳ
   - Các bảng này chứa ngữ nghĩa nghiệp vụ

2. **Bảng trung tâm: `student_wallet_ledger`**
   - Mỗi biến động tiền tạo 1 hoặc nhiều record trong ledger
   - Cấu trúc:
     - `ledger_id`: ID duy nhất
     - `student_id`: Sinh viên
     - `amount`: Số tiền (+ cho IN, - cho OUT)
     - `direction`: 'IN' hoặc 'OUT'
     - `source_type`: 'DEPOSIT', 'SEMESTER_BONUS', 'PAYMENT', 'REFUND'
     - `source_table`: Tên bảng nguồn (ví dụ: 'deposit', 'payment')
     - `source_id`: ID của record trong bảng nguồn
     - `description`: Mô tả người đọc được
     - `created_at`: Thời gian tạo

3. **Cách hoạt động:**

   **Khi nạp tiền:**
   - Tạo record trong `deposit`
   - Tạo 2 ledger entries:
     - `+deposit_amount` (IN, DEPOSIT)
     - `+bonus_amount` (IN, DEPOSIT) nếu có bonus

   **Khi thanh toán:**
   - Tạo record trong `payment`
   - Tạo 1 ledger entry:
     - `-amount_paid_from_balance` (OUT, PAYMENT) - chỉ phần trả từ số dư

   **Khi refund:**
   - Tạo record trong `refund_print_job`
   - Tạo 1 ledger entry:
     - `+refund_amount` (IN, REFUND)

   **Khi nhận bonus học kỳ:**
   - Tạo record trong `student_semester_bonus`
   - Tạo 1 ledger entry:
     - `+bonus_amount` (IN, SEMESTER_BONUS)

4. **Lợi ích của Ledger Pattern:**
   - **Audit trail hoàn chỉnh:** Mọi biến động tiền đều được ghi lại
   - **Tính toán số dư nhanh:** `SUM(amount) WHERE student_id = X`
   - **Lịch sử giao dịch:** Query ledger để xem lịch sử chi tiết
   - **Dễ debug:** Dễ dàng trace lại từng giao dịch
   - **Tương thích với hệ thống tài chính:** Pattern chuẩn trong ngân hàng, ví điện tử

5. **Sử dụng Ledger:**
   - **Tính số dư:** `SELECT SUM(amount) FROM student_wallet_ledger WHERE student_id = @student_id`
   - **Lịch sử giao dịch:** `SELECT * FROM student_wallet_ledger WHERE student_id = @student_id ORDER BY created_at DESC`
   - **View `student_balance_view`** vẫn hoạt động bình thường (tính từ domain tables), nhưng có thể thay thế bằng query ledger để tối ưu hiệu năng

---

### 7. CẤU HÌNH GIÁ

**Mục đích:** Quản lý cấu hình giá cho các dịch vụ in.

**Bảng chính:**
- `color_mode`: Định nghĩa chế độ màu (color, grayscale, black-white)
- `color_mode_price`: Giá cho mỗi chế độ màu (price_per_page)
- `page_size`: Kích thước giấy (A3, A4, A5)
- `page_size_price`: Giá cho mỗi kích thước giấy (page_price)
- `page_discount_package`: Gói giảm giá khối lượng (ví dụ: 100 trang giảm 10%)
- `print_job`: Công việc in tham chiếu đến các cấu hình giá

**CÁCH TÍNH GIÁ CHO PRINT JOB:**

**Bước 1: Xác định giá cơ bản**
- Lấy `color_mode_price.price_per_page` từ `color_mode_price_id` trong `print_job`
- Đây là giá mỗi trang cho chế độ màu được chọn

**Bước 2: Tính tổng tiền trước giảm giá**
```
subtotal_before_discount = total_pages × color_mode_price_per_page
```
Trong đó:
- `total_pages` = số trang từ `print_job_page` × `number_of_copy`

**Bước 3: Áp dụng giảm giá khối lượng (nếu có)**
- Kiểm tra `page_discount_package_id` trong `print_job`
- Nếu có, lấy `discount_percentage` từ `page_discount_package`
- Tính: `discount_amount = subtotal_before_discount × discount_percentage`

**Bước 4: Tính tổng tiền cuối cùng**
```
total_price = subtotal_before_discount - discount_amount
```

**Ví dụ:**

Print job với:
- 50 trang, 2 bản sao → `total_pages = 100`
- `color_mode_price_id` → giá $0.30/trang (color)
- `page_discount_package_id` → giảm 10% (cho 100+ trang)

Tính toán:
- `subtotal_before_discount` = 100 × $0.30 = $30.00
- `discount_amount` = $30.00 × 0.10 = $3.00
- `total_price` = $30.00 - $3.00 = $27.00

**TẠI SAO LƯU GIÁ TRONG PRINT_JOB?**

Tất cả các giá trị được lưu trong `print_job` để:
1. **Tính lịch sử:** Khi giá thay đổi sau này, các công việc in cũ vẫn giữ nguyên giá đã áp dụng
2. **Hiệu suất:** Tránh phải tính toán lại mỗi lần truy vấn
3. **Audit:** Có thể kiểm tra chính xác giá nào đã được áp dụng tại thời điểm tạo job

**Cách tham chiếu:**
- `print_job.page_size_price_id` → `page_size_price.price_id` → biết giá kích thước trang
- `print_job.color_mode_price_id` → `color_mode_price.setting_id` → biết giá chế độ màu
- `print_job.page_discount_package_id` → `page_discount_package.package_id` → biết gói giảm giá

**Lưu ý:** `color_mode_price` tham chiếu đến `color_mode` để biết chế độ màu nào, tương tự `page_size_price` tham chiếu đến `page_size`.

---

### 8. MUA GIẤY & QUẢN LÝ KHO

**Mục đích:** Quản lý việc mua giấy và nguồn vốn.

**Bảng chính:**
- `fund_source`: Nguồn vốn (ngân sách trường, quyên góp, doanh thu, etc.)
- `supplier_paper_purchase`: Đơn mua giấy từ nhà cung cấp
- `paper_purchase_item`: Chi tiết từng loại giấy trong đơn mua
- `page_size`: Kích thước giấy được mua
- `staff`: Nhân viên thực hiện mua hàng

**Cách hoạt động:**
- `fund_source` ghi nhận các nguồn tiền vào hệ thống
- `supplier_paper_purchase` là đơn mua giấy từ nhà cung cấp
- `paper_purchase_item` chi tiết từng loại giấy (kích thước, số lượng, giá)
- Hỗ trợ tracking số lượng đã nhận (`received_quantity`, `received_date`)

---

### 9. CẤU HÌNH HỆ THỐNG

**Mục đích:** Quản lý các cấu hình hệ thống.

**Bảng chính:**
- `system_configuration`: Các cấu hình hệ thống (key-value pairs)
- `permitted_file_type`: Các loại file được phép upload
- `staff`: Nhân viên quản lý cấu hình

**Cách hoạt động:**
- `system_configuration` lưu các cấu hình dạng key-value (ví dụ: max_file_size_mb, queue_timeout_minutes)
- `permitted_file_type` định nghĩa các extension file được phép (pdf, docx, jpg, etc.)
- Có thể bật/tắt từng loại file thông qua `is_permitted`

---

### 10. KIỂM TRA & GHI NHẬT KÝ

**Mục đích:** Ghi nhận các hoạt động và lỗi trong hệ thống.

**Bảng chính:**
- `printer_log`: Log của máy in (print job, lỗi, bảo trì, thay đổi trạng thái)
- `system_audit_log`: Audit log của hệ thống (thay đổi dữ liệu, hành động của user)
- `user`: User thực hiện hành động
- `printer_physical`: Máy in liên quan
- `print_job`: Công việc in liên quan

**Cách hoạt động:**
- `printer_log` ghi nhận các sự kiện liên quan đến máy in (lỗi, bảo trì, print job)
- `system_audit_log` ghi nhận các thay đổi dữ liệu quan trọng (CRUD operations)
- Hỗ trợ tracking lỗi và giải quyết (`is_resolved`, `resolved_by`, `resolution_notes`)
- Có thể lưu thông tin chi tiết dạng JSON trong `details` field

---

## HƯỚNG DẪN SỬ DỤNG CHO DEVELOPERS

### HIỂN THỊ SỐ DƯ CHO USER

**KHÔNG BAO GIỜ** lưu số dư trong bảng `student`. Luôn tính toán từ các transaction:

```sql
-- Cách 1: Sử dụng VIEW (KHUYẾN NGHỊ)
SELECT balance_amount 
FROM student_balance_view 
WHERE student_id = @student_id;

-- Cách 2: Tính toán trực tiếp
SELECT 
    COALESCE((
        SELECT SUM(total_credited)
        FROM deposit
        WHERE student_id = @student_id AND payment_status = 'completed'
    ), 0) +
    COALESCE((
        SELECT SUM(sb.bonus_amount)
        FROM student_semester_bonus ssb
        JOIN semester_bonus sb ON ssb.semester_bonus_id = sb.bonus_id
        WHERE ssb.student_id = @student_id AND ssb.received = 1
    ), 0) -
    COALESCE((
        SELECT SUM(amount_paid_from_balance)
        FROM payment
        WHERE student_id = @student_id AND payment_status = 'completed'
    ), 0) AS balance;
```

**Kiểm tra đủ tiền để thanh toán:**
```sql
DECLARE @required_amount DECIMAL(10,2) = 27.00; -- Giá print job
DECLARE @current_balance DECIMAL(10,2);

SELECT @current_balance = balance_amount 
FROM student_balance_view 
WHERE student_id = @student_id;

IF @current_balance >= @required_amount
BEGIN
    -- Đủ tiền, cho phép thanh toán
END
ELSE
BEGIN
    -- Không đủ tiền, yêu cầu nạp thêm
END
```

---

### TẠO PRINT JOB MỚI

**Bước 1: Xác định cấu hình giá**
```sql
-- Lấy page_size_price_id dựa trên page_size được chọn
SELECT price_id 
FROM page_size_price 
WHERE page_size_id = @selected_page_size_id 
  AND is_active = 1;

-- Lấy color_mode_price_id dựa trên color_mode được chọn
SELECT setting_id 
FROM color_mode_price 
WHERE color_mode_id = @selected_color_mode_id 
  AND is_active = 1;
```

**Bước 2: Đếm số trang từ file**
- Parse file (PDF, DOCX, etc.) để đếm số trang
- Tạo records trong `print_job_page` cho mỗi trang

**Bước 3: Tính giá**
```sql
DECLARE @total_pages INT = (SELECT COUNT(*) FROM print_job_page WHERE job_id = @job_id) * @number_of_copy;
DECLARE @color_mode_price_per_page DECIMAL(10,4);
DECLARE @subtotal DECIMAL(10,2);
DECLARE @discount_percentage DECIMAL(5,4);
DECLARE @discount_amount DECIMAL(10,2);
DECLARE @total_price DECIMAL(10,2);

-- Lấy giá chế độ màu
SELECT @color_mode_price_per_page = price_per_page 
FROM color_mode_price 
WHERE setting_id = @color_mode_price_id;

-- Tính subtotal
SET @subtotal = @total_pages * @color_mode_price_per_page;

-- Tìm gói giảm giá phù hợp
SELECT TOP 1 
    @page_discount_package_id = package_id,
    @discount_percentage = discount_percentage
FROM page_discount_package
WHERE min_pages <= @total_pages 
  AND is_active = 1
ORDER BY min_pages DESC;

-- Tính discount và total
SET @discount_amount = @subtotal * ISNULL(@discount_percentage, 0);
SET @total_price = @subtotal - @discount_amount;
```

**Bước 4: Tạo print_job record**
```sql
INSERT INTO print_job (
    job_id, student_id, printer_id, uploaded_file_id,
    page_size_price_id, color_mode_price_id, page_discount_package_id,
    page_orientation, print_side, number_of_copy,
    total_pages, subtotal_before_discount, discount_percentage, 
    discount_amount, total_price, print_status, created_at
) VALUES (
    @job_id, @student_id, @printer_id, @uploaded_file_id,
    @page_size_price_id, @color_mode_price_id, @page_discount_package_id,
    @page_orientation, @print_side, @number_of_copy,
    @total_pages, @subtotal, @discount_percentage,
    @discount_amount, @total_price, 'queued', GETDATE()
);
```

---

### THANH TOÁN CHO PRINT JOB

**Bước 1: Kiểm tra số dư**
```sql
DECLARE @balance DECIMAL(10,2);
SELECT @balance = balance_amount 
FROM student_balance_view 
WHERE student_id = @student_id;

DECLARE @job_price DECIMAL(10,2);
SELECT @job_price = total_price 
FROM print_job 
WHERE job_id = @job_id;
```

**Bước 2: Xác định phương thức thanh toán**
```sql
DECLARE @amount_from_balance DECIMAL(10,2);
DECLARE @amount_directly DECIMAL(10,2);
DECLARE @payment_method VARCHAR(50);

IF @balance >= @job_price
BEGIN
    -- Đủ số dư, thanh toán hoàn toàn từ số dư
    SET @amount_from_balance = @job_price;
    SET @amount_directly = 0;
    SET @payment_method = 'balance';
END
ELSE IF @balance > 0
BEGIN
    -- Một phần từ số dư, phần còn lại trực tiếp
    SET @amount_from_balance = @balance;
    SET @amount_directly = @job_price - @balance;
    SET @payment_method = 'credit_card'; -- hoặc phương thức user chọn
END
ELSE
BEGIN
    -- Không có số dư, thanh toán hoàn toàn trực tiếp
    SET @amount_from_balance = 0;
    SET @amount_directly = @job_price;
    SET @payment_method = 'credit_card'; -- hoặc phương thức user chọn
END
```

**Bước 3: Tạo payment record**
```sql
INSERT INTO payment (
    payment_id, job_id, student_id,
    amount_paid_directly, amount_paid_from_balance, total_amount,
    payment_method, payment_reference, payment_status, transaction_date
) VALUES (
    NEWID(), @job_id, @student_id,
    @amount_directly, @amount_from_balance, @job_price,
    @payment_method, @payment_reference, 'completed', GETDATE()
);
```

**Lưu ý:** Sau khi tạo payment với `payment_status = 'completed'`, số dư của sinh viên sẽ tự động giảm khi query từ `student_balance_view`.

---

### CẬP NHẬT GIÁ (CHO ADMIN)

**Khi cần thay đổi giá:**

1. **Tạo cấu hình giá mới** (không xóa cấu hình cũ):
```sql
-- Ví dụ: Tăng giá color mode
INSERT INTO color_mode_price (
    setting_id, color_mode_id, price_per_page, is_active, created_at, updated_at
) VALUES (
    NEWID(), @color_mode_id, 0.35, 1, GETDATE(), GETDATE()
);

-- Đánh dấu cấu hình cũ là không active
UPDATE color_mode_price 
SET is_active = 0, updated_at = GETDATE()
WHERE color_mode_id = @color_mode_id 
  AND setting_id != @new_setting_id;
```

2. **Các print job mới sẽ sử dụng giá mới** (vì query `is_active = 1`)
3. **Các print job cũ giữ nguyên giá** (vì đã lưu `color_mode_price_id` cụ thể)

---

### TRUY VẤN LỊCH SỬ IN CỦA SINH VIÊN

```sql
-- Sử dụng view có sẵn
SELECT 
    job_id, student_code, student_name,
    paper_size, print_side, color_mode, number_of_copy,
    page_count, total_pages,
    printer_brand, printer_model, campus_name, room_code,
    print_status, start_time, end_time
FROM student_printing_history
WHERE student_id = @student_id
ORDER BY created_at DESC;
```

---

### TRUY VẤN CHI TIẾT GIÁ CỦA PRINT JOB

```sql
-- Sử dụng view print_job_pricing
SELECT 
    job_id,
    paper_size_id,
    base_price_per_page,
    color_mode_price_per_page,
    total_pages,
    subtotal_before_discount,
    discount_percentage,
    discount_amount,
    total_price
FROM print_job_pricing
WHERE job_id = @job_id;
```

---

## CÁC VIEW QUAN TRỌNG

1. **`student_balance_view`**: Tính số dư của sinh viên
2. **`student_printing_history`**: Lịch sử in của sinh viên với đầy đủ thông tin
3. **`print_job_pricing`**: Chi tiết giá của print job
4. **`printer_usage_statistic`**: Thống kê sử dụng máy in
5. **`active_printer_detail`**: Chi tiết các máy in đang hoạt động
6. **`daily_printing_activity`**: Hoạt động in theo ngày
7. **`monthly_report`**: Báo cáo theo tháng
8. **`yearly_report`**: Báo cáo theo năm

---

## LƯU Ý QUAN TRỌNG

1. **Số dư:** Luôn tính toán từ transactions, KHÔNG lưu trong bảng
2. **Giá:** Luôn lưu trong `print_job` để đảm bảo tính lịch sử
3. **Cấu hình giá:** Tạo mới và đánh dấu cũ là `is_active = 0`, không xóa
4. **Foreign keys:** Luôn tham chiếu đến các bảng cấu hình để biết giá tại thời điểm tạo job
5. **Views:** Sử dụng views có sẵn cho các truy vấn phổ biến
6. **Test accounts:** Có đủ dữ liệu để demo tất cả chức năng (20-30 print jobs, đầy đủ các trạng thái và cấu hình)

---

## TEST ACCOUNTS

Các tài khoản test được đảm bảo có đủ dữ liệu:
- `student.test@edu.vn` (TEST001)
- `phandienmanhthienk16@siu.edu.vn` (TEST002)
- `leanhtuank16@siu.edu.vn` (TEST003)
- `nguyenhongbaongock16@siu.edu.vn` (TEST004)

Mỗi account có:
- 20-30 print jobs với đầy đủ các trạng thái, chế độ màu, kích thước trang
- 2-4 deposits đã hoàn thành
- Tất cả semester bonuses đã nhận
- Tất cả print jobs đều có payment đã hoàn thành

