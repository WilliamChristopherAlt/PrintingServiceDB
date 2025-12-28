# NHẬT KÝ THAY ĐỔI: BẢNG `student_wallet_ledger`
## Smart Printing Service System (SSPS)

---

## BẢNG `student_wallet_ledger` - KIẾN TRÚC LEDGER PATTERN

### Thay đổi:
- **THÊM bảng:** `student_wallet_ledger`
- **Các cột:**
  - `ledger_id` (UNIQUEIDENTIFIER, PK)
  - `student_id` (UNIQUEIDENTIFIER, FK → `student.student_id`)
  - `amount` (DECIMAL(10,2), NOT NULL) – số tiền (+ cho IN, - cho OUT)
  - `direction` (VARCHAR(3), NOT NULL, CHECK IN ('IN', 'OUT')) – hướng giao dịch
  - `source_type` (VARCHAR(20), NOT NULL, CHECK IN ('DEPOSIT', 'SEMESTER_BONUS', 'PAYMENT', 'REFUND')) – loại giao dịch
  - `source_table` (VARCHAR(50), NOT NULL) – tên bảng nguồn (ví dụ: 'deposit', 'payment')
  - `source_id` (UNIQUEIDENTIFIER, NOT NULL) – ID của record trong bảng nguồn
  - `description` (NVARCHAR(255)) – mô tả người đọc được
  - `created_at` (DATETIME)
- **THÊM indexes:**
  - `idx_ledger_student` trên `student_id`
  - `idx_ledger_student_created` trên `(student_id, created_at)`
  - `idx_ledger_source` trên `(source_table, source_id)`
  - `idx_ledger_source_type` trên `source_type`
  - `idx_ledger_direction` trên `direction`
  - `idx_ledger_created_at` trên `created_at`

### Lý do:
Triển khai **kiến trúc Ledger Pattern** (sổ cái) để quản lý số dư sinh viên:

1. **Pattern chuẩn trong hệ thống tài chính:**
   - Được sử dụng rộng rãi trong ví điện tử, ngân hàng số, SaaS có billing
   - Mỗi biến động tiền tạo một hoặc nhiều record trong ledger
   - Cung cấp audit trail hoàn chỉnh

2. **Cách hoạt động:**
   - **Khi nạp tiền:** Tạo 2 ledger entries:
     - `+deposit_amount` (IN, DEPOSIT)
     - `+bonus_amount` (IN, DEPOSIT) nếu có bonus
   - **Khi thanh toán:** Tạo 1 ledger entry:
     - `-amount_paid_from_balance` (OUT, PAYMENT) – chỉ phần trả từ số dư
   - **Khi refund:** Tạo 1 ledger entry:
     - `+refund_amount` (IN, REFUND)
   - **Khi nhận bonus học kỳ:** Tạo 1 ledger entry:
     - `+bonus_amount` (IN, SEMESTER_BONUS)

3. **Lợi ích:**
   - **Audit trail hoàn chỉnh:** Mọi biến động tiền đều được ghi lại với timestamp và mô tả
   - **Tính toán số dư nhanh:** `SELECT SUM(amount) FROM student_wallet_ledger WHERE student_id = @student_id`
   - **Lịch sử giao dịch:** Dễ dàng query lịch sử chi tiết theo thời gian
   - **Dễ debug:** Trace lại từng giao dịch thông qua `source_table` và `source_id`
   - **Tương thích:** Pattern chuẩn, dễ tích hợp với hệ thống tài chính bên ngoài

4. **Bảng domain giữ nguyên:**
   - Các bảng `deposit`, `payment`, `refund_print_job`, `student_semester_bonus` vẫn giữ nguyên
   - Chúng chứa ngữ nghĩa nghiệp vụ
   - Ledger chỉ là lớp ghi lại biến động tiền

5. **View `student_balance_view`:**
   - View hiện tại vẫn hoạt động bình thường (tính từ domain tables)
   - Có thể thay thế bằng query ledger để tối ưu hiệu năng trong tương lai
   - Ledger và view có thể tồn tại song song

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi tạo giao dịch tài chính:
- **Khi nạp tiền:** Sau khi tạo record trong `deposit`, phải tạo 2 ledger entries:
  - Entry cho `deposit_amount` (IN, DEPOSIT)
  - Entry cho `bonus_amount` (IN, DEPOSIT) nếu có
- **Khi thanh toán:** Sau khi tạo record trong `payment`, phải tạo 1 ledger entry:
  - Entry cho `amount_paid_from_balance` (OUT, PAYMENT) nếu > 0
- **Khi refund:** Sau khi tạo record trong `refund_print_job`, phải tạo 1 ledger entry:
  - Entry cho refund amount (IN, REFUND)
- **Khi nhận bonus học kỳ:** Sau khi cập nhật `student_semester_bonus.received = 1`, phải tạo 1 ledger entry:
  - Entry cho `bonus_amount` (IN, SEMESTER_BONUS)

### Khi tính số dư:
- Có thể sử dụng view `student_balance_view` (tính từ domain tables)
- Hoặc query trực tiếp từ ledger: `SELECT SUM(amount) FROM student_wallet_ledger WHERE student_id = @student_id`
- Ledger cung cấp cách tính nhanh hơn và audit trail đầy đủ hơn

---

## NGÀY THỰC HIỆN
Thay đổi được thực hiện: [Ngày hiện tại]

---

## GHI CHÚ
- Bảng `student_wallet_ledger` đã được thêm vào `design.sql`
- Script sinh dữ liệu (`generate.py`) đã được cập nhật để tạo ledger entries
- Diagram module "Quản lý Thanh toán & Số dư" đã được cập nhật để bao gồm bảng ledger
- DEVELOPER_GUIDE.md đã được cập nhật với giải thích về Ledger Pattern

