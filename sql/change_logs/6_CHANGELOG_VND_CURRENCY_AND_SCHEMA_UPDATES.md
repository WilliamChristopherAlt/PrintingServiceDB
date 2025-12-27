# NHẬT KÝ THAY ĐỔI: CHUYỂN ĐỔI TIỀN TỆ SANG VND VÀ CẬP NHẬT SCHEMA
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN

Changelog này ghi lại các thay đổi lớn về:
1. Chuyển đổi toàn bộ hệ thống tiền tệ từ USD sang VND (Vietnamese Dong)
2. Cập nhật schema để phù hợp với design mới (loại bỏ các trường không cần thiết, thêm các tính năng mới)
3. Thay đổi pricing model từ direct price sang multiplier cho color modes
4. Thêm bảng notification và các tính năng thanh toán mới

---

## THAY ĐỔI CHI TIẾT

### 1. CHUYỂN ĐỔI TIỀN TỆ TỪ USD SANG VND

#### 1.1. Thay đổi kiểu dữ liệu DECIMAL

**Trước:** `DECIMAL(10, 2)` cho USD (ví dụ: $10.50)
**Sau:** `DECIMAL(15, 0)` hoặc `DECIMAL(18, 0)` cho VND (ví dụ: 10000 VND)

**Bảng bị ảnh hưởng:**
- `deposit_bonus_package.amount_cap`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `deposit.deposit_amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `deposit.bonus_amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `deposit.total_credited`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `semester_bonus.bonus_amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `page_size_price.page_price`: `DECIMAL(10, 4)` → `DECIMAL(15, 0)`
- `print_job.subtotal_before_discount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `print_job.discount_amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `print_job.total_price`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `payment.amount_paid_directly`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `payment.amount_paid_from_balance`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `payment.total_amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `student_wallet_ledger.amount`: `DECIMAL(10, 2)` → `DECIMAL(15, 0)`
- `fund_source.amount`: `DECIMAL(12, 2)` → `DECIMAL(18, 0)`
- `supplier_paper_purchase.total_amount_paid`: `DECIMAL(12, 2)` → `DECIMAL(18, 0)`
- `paper_purchase_item.unit_price`: `DECIMAL(10, 4)` → `DECIMAL(15, 0)`
- `paper_purchase_item.total_price`: `DECIMAL(12, 2)` → `DECIMAL(18, 0)`

#### 1.2. Cập nhật giá mặc định

**Page Size Prices:**
- A4: 1000 VND/trang (trước: $0.20)
- A3: 2000 VND/trang (trước: $0.40)
- A5: 500 VND/trang (trước: $0.10)

**Color Mode Multipliers:**
- Black-white: 0.5x (giá cuối: 500 VND/trang cho A4)
- Grayscale: 0.75x (giá cuối: 750 VND/trang cho A4)
- Color: 1.5x (giá cuối: 1500 VND/trang cho A4)

**Semester Bonus:**
- 125,000 VND/semester (trước: $5)

**Deposit Amounts:**
- Range: 125,000 - 2,500,000 VND (trước: $5 - $100)

#### 1.3. Cập nhật comments

Tất cả comments liên quan đến "dollars", "$", "USD" đã được thay đổi thành "VND" hoặc "vnd".

---

### 2. CẬP NHẬT SCHEMA - BẢNG `deposit_bonus_package`

#### Thay đổi:
- **XÓA cột:** `code VARCHAR(20) NOT NULL UNIQUE`
- **XÓA cột:** `is_event BIT DEFAULT 0`
- **XÓA index:** `idx_deposit_bonus_package_code`

#### Lý do:
- Đơn giản hóa schema, không cần code riêng cho từng package
- Loại bỏ tính năng event package không cần thiết

---

### 3. CẬP NHẬT SCHEMA - BẢNG `deposit`

#### Thay đổi:
- **XÓA cột:** `deposit_code VARCHAR(8) NOT NULL UNIQUE`
- **XÓA cột:** `expired_at DATETIME NULL`
- **XÓA cột:** `cancellation_reason NVARCHAR(500) NULL`
- **XÓA status:** `'expired'` và `'cancelled'` khỏi CHECK constraint
- **XÓA index:** `idx_deposit_code`
- **XÓA index:** `idx_deposit_expired_at`
- **XÓA index:** `idx_deposit_student_status_expired`
- **CẬP NHẬT comment:** "real dollars" → "real VND"

#### Lý do:
- Đơn giản hóa flow nạp tiền, không cần code riêng
- Loại bỏ tính năng expiration và cancellation không cần thiết
- Giảm complexity của hệ thống

---

### 4. CẬP NHẬT SCHEMA - BẢNG `color_mode_price`

#### Thay đổi:
- **ĐỔI cột:** `price_per_page DECIMAL(15, 0)` → `price_multiplier DECIMAL(5, 4)`
- **CẬP NHẬT comment:** Từ "Price per page" sang "Multiplier applied to base page_size_price"

#### Lý do:
- Pricing model linh hoạt hơn: giá = base_price × multiplier
- Dễ dàng điều chỉnh giá khi base price thay đổi
- Phù hợp với business logic: color mode là hệ số nhân, không phải giá cố định

#### Giá trị mặc định:
- Black-white: 0.5x
- Grayscale: 0.75x
- Color: 1.5x

---

### 5. CẬP NHẬT SCHEMA - BẢNG `uploaded_file`

#### Thay đổi:
- **THÊM cột:** `page_count INT NULL`
- **THÊM index:** `idx_uploaded_file_page_count`
- **CẬP NHẬT comment:** Giải thích cách tính page_count (PDFBox cho PDF, ConvertAPI + PDFBox cho DOCX/DOC, POI cho Office files)

#### Lý do:
- Cần biết số trang của file để hiển thị thông tin cho người dùng
- Hỗ trợ tính toán chi phí và quản lý tài nguyên tốt hơn

---

### 6. CẬP NHẬT SCHEMA - BẢNG `print_job`

#### Thay đổi:
- **THÊM cột:** `payment_method VARCHAR(50) NULL`
  - Comment: "Payment method selected when creating job: 'balance' or 'qr' (SePay)"
- **THÊM status:** `'pending_payment'` vào CHECK constraint
- **CẬP NHẬT:** Tất cả DECIMAL money fields từ `DECIMAL(10, 2)` → `DECIMAL(15, 0)`

#### Lý do:
- Cần biết phương thức thanh toán khi tạo job
- Hỗ trợ thanh toán QR code qua SePay
- Status `pending_payment` cho phép tạo job trước khi thanh toán

---

### 7. CẬP NHẬT SCHEMA - BẢNG `payment`

#### Thay đổi:
- **THÊM cột:** `payment_code VARCHAR(20) NULL`
  - Comment: "Payment code for QR code (format: SIUJOB + 8 chars)"
- **THÊM cột:** `expired_at DATETIME NULL`
  - Comment: "Expiration time for QR payment"
- **THÊM status:** `'expired'` vào CHECK constraint
- **THÊM index:** `idx_payment_code`
- **THÊM index:** `idx_payment_expired_at`
- **CẬP NHẬT:** Tất cả DECIMAL money fields từ `DECIMAL(10, 2)` → `DECIMAL(15, 0)`

#### Lý do:
- Hỗ trợ thanh toán QR code với payment code riêng
- Quản lý expiration time cho QR payments
- Cần index để query nhanh theo payment_code và expired_at

---

### 8. THÊM BẢNG MỚI - `notification`

#### Bảng mới:
```sql
CREATE TABLE notification (
    notification_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    title NVARCHAR(200) NOT NULL,
    message NVARCHAR(1000) NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);
```

#### Indexes:
- `idx_notification_student`: (student_id, created_at)
- `idx_notification_unread`: (student_id, is_read, created_at)

#### Lý do:
- Thông báo cho sinh viên về các sự kiện: nạp tiền thành công, print job hoàn thành/thất bại, etc.
- Hỗ trợ real-time notifications trong ứng dụng

---

### 9. CẬP NHẬT VIEW - `student_balance_view`

#### Thay đổi:
- **TRƯỚC:** Tính balance từ nhiều nguồn (deposits, semester bonuses, payments, refunds)
- **SAU:** Tính balance từ `student_wallet_ledger` (single source of truth)

#### Code mới:
```sql
CREATE VIEW student_balance_view AS
SELECT 
    s.student_id,
    s.student_code,
    u.full_name,
    u.email,
    COALESCE((
        SELECT SUM(swl.amount)
        FROM student_wallet_ledger swl
        WHERE swl.student_id = s.student_id
    ), 0) AS balance_amount
FROM student s
JOIN [user] u ON s.user_id = u.user_id;
```

#### Lý do:
- `student_wallet_ledger` là single source of truth cho tất cả transactions
- Đảm bảo tính nhất quán và bao gồm cả manual adjustments
- Đơn giản hóa logic tính toán balance

---

### 10. CẬP NHẬT VIEW - `print_job_pricing`

#### Thay đổi:
- **TRƯỚC:** `cmp.price_per_page AS color_mode_price_per_page`
- **SAU:** `cmp.price_multiplier AS color_mode_price_multiplier`

#### Lý do:
- Phù hợp với thay đổi schema từ `price_per_page` sang `price_multiplier`

---

### 11. CẬP NHẬT INDEXES - `print_job`

#### Thay đổi:
- **THÊM composite index:** `idx_print_job_printer_status_created` (printer_id, print_status, created_at)
  - Comment: "Composite index for queue queries (optimize finding queued/printing jobs by printer)"
- **THÊM index:** `idx_print_job_status_start_time` (print_status, start_time)
  - Comment: "Index for progress queries (optimize finding printing jobs)"

#### Lý do:
- Tối ưu hiệu suất cho các query tìm jobs theo printer và status
- Cải thiện performance cho progress tracking queries

---

## MIGRATION NOTES

### Dữ liệu cần migrate:

1. **Chuyển đổi tiền tệ:**
   - Tất cả giá trị tiền cần nhân với tỷ lệ chuyển đổi (ví dụ: 1 USD = 25,000 VND)
   - Tuy nhiên, trong trường hợp này, giá mới được set lại hoàn toàn:
     - A4: 1000 VND (không phải convert từ $0.20)
     - Deposit amounts: 125,000 - 2,500,000 VND (không phải convert từ $5-$100)

2. **Xóa dữ liệu không còn hợp lệ:**
   - Xóa các deposit có status `'expired'` hoặc `'cancelled'` (nếu có)
   - Xóa các deposit_bonus_package có `code` hoặc `is_event` (nếu cần)

3. **Cập nhật color_mode_price:**
   - Chuyển từ giá trực tiếp sang multiplier
   - Ví dụ: Nếu trước đó có `price_per_page = 2000`, cần tính lại:
     - Base A4 = 1000 VND
     - Multiplier = 2000 / 1000 = 2.0

4. **Tạo dữ liệu mới:**
   - Thêm các notification records nếu cần
   - Cập nhật payment records với `payment_code` và `expired_at` nếu có QR payments

---

## BREAKING CHANGES

### API Changes:
- Tất cả endpoints trả về money values sẽ trả về VND thay vì USD
- Response format không thay đổi, chỉ giá trị thay đổi

### Database Changes:
- Các query sử dụng `deposit.deposit_code` sẽ fail (cột đã bị xóa)
- Các query sử dụng `deposit.expired_at` hoặc `deposit.cancellation_reason` sẽ fail
- Các query sử dụng `color_mode_price.price_per_page` sẽ fail (đổi thành `price_multiplier`)
- Các query tính balance từ deposits/payments trực tiếp cần chuyển sang dùng `student_wallet_ledger`

### Application Changes:
- Frontend cần hiển thị "VND" thay vì "$" hoặc "USD"
- Pricing calculation logic cần update: `price = base_price × multiplier` thay vì dùng giá trực tiếp
- Payment flow cần hỗ trợ `payment_code` và `expired_at` cho QR payments

---

## TESTING CHECKLIST

- [ ] Verify all money values are in VND range (không có giá trị quá nhỏ như 0.01)
- [ ] Verify pricing calculation: base_price × multiplier = final_price
- [ ] Verify deposit flow không còn dùng deposit_code
- [ ] Verify payment flow hỗ trợ payment_code và expired_at
- [ ] Verify notification system hoạt động đúng
- [ ] Verify student_balance_view tính đúng từ ledger
- [ ] Verify print_job có thể tạo với status 'pending_payment'
- [ ] Verify color mode multipliers áp dụng đúng (0.5x, 0.75x, 1.5x)

---

## FILES CHANGED

- `sql/design.sql` - Schema updates
- `pipeline/generate.py` - Data generation updates
- `sql/insert.sql` - Regenerated với giá trị VND mới

---

## DATE
2025-01-XX

---

## AUTHOR
System Migration

