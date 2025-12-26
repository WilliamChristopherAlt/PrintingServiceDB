# NHẬT KÝ THAY ĐỔI: CẬP NHẬT SCHEMA DEPOSIT VÀ HẠN CHẾ DỮ LIỆU TEST
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN

Changelog này ghi lại các thay đổi về:
1. Cập nhật schema bảng `deposit` với các trường mới (deposit_code, expired_at, cancellation_reason)
2. Hạn chế data generation chỉ cho hard-coded test accounts
3. Cập nhật print job generation với tỷ lệ completed cao và dates trong quá khứ
4. Hạn chế staff creation chỉ sử dụng test staff

**Ngày:** 2025-01-XX
**Phiên bản:** 7.0

---

## THAY ĐỔI CHI TIẾT

### 1. CẬP NHẬT SCHEMA BẢNG `deposit`

#### 1.1. Thêm các trường mới

**Bảng:** `deposit`

**Các trường được thêm:**
- `deposit_code VARCHAR(8) NOT NULL UNIQUE` - Mã ngắn gọn 8 ký tự để hiển thị trong nội dung chuyển khoản
- `expired_at DATETIME NULL` - Thời gian hết hạn của mã QR (10 phút sau khi tạo)
- `cancellation_reason NVARCHAR(500) NULL` - Lý do hủy đơn (nếu có)

**Cập nhật CHECK constraint:**
- `payment_status` CHECK constraint được mở rộng để bao gồm:
  - `'pending'` (mặc định)
  - `'completed'`
  - `'failed'`
  - `'refunded'`
  - `'expired'` (mới)
  - `'cancelled'` (mới)

**Index mới:**
- `idx_deposit_code` - Index trên `deposit_code` để tối ưu lookup

#### 1.2. SQL Schema Changes

```sql
-- Thêm các trường mới
ALTER TABLE deposit ADD deposit_code VARCHAR(8) NOT NULL UNIQUE;
ALTER TABLE deposit ADD expired_at DATETIME NULL;
ALTER TABLE deposit ADD cancellation_reason NVARCHAR(500) NULL;

-- Cập nhật CHECK constraint
ALTER TABLE deposit DROP CONSTRAINT [tên constraint cũ];
ALTER TABLE deposit ADD CONSTRAINT chk_deposit_payment_status 
    CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded', 'expired', 'cancelled'));

-- Thêm index
CREATE INDEX idx_deposit_code ON deposit (deposit_code);
```

---

### 2. HẠN CHẾ DATA GENERATION CHO TEST ACCOUNTS

#### 2.1. Deposit Generation

**Trước:**
- 30% students ngẫu nhiên có deposits
- Test accounts: 20 deposits mỗi account
- Regular students: 1-3 deposits mỗi account

**Sau:**
- **CHỈ** hard-coded test accounts có deposits
- Test accounts: **5-9 deposits** mỗi account (random)
- Loại trừ: `leanhtuank16@siu.edu.vn` (không có deposits/payments)

**Hard-coded test accounts:**
- `student.test@edu.vn`
- `phandienmanhthienk16@siu.edu.vn`
- `nguyenhongbaongock16@siu.edu.vn`
- `phanthanhthaituank16@siu.edu.vn`
- `lengocdangkhoak16@siu.edu.vn`
- `lyhieuvyk17@siu.edu.vn`

**Deposit fields được generate:**
- `deposit_code`: Unique 8-character alphanumeric code (A-Z, 0-9)
- `expired_at`: 10 phút sau `transaction_date` nếu status là `'expired'` hoặc `'pending'`
- `cancellation_reason`: Random reason nếu status là `'cancelled'`

**Payment status distribution:**
- 90% `'completed'`
- 5% `'pending'`
- 3% `'failed'`
- 1% `'expired'`
- 1% `'cancelled'`

**Transaction dates:**
- Phân bố ngẫu nhiên trong **6 tháng gần nhất** (180 days ago to now)

#### 2.2. Print Job Generation

**Trước:**
- Tất cả students có print jobs
- Test accounts: 20 jobs mỗi account
- Regular students: Số lượng dựa trên Gaussian distribution
- Status distribution theo spec
- Dates: Trong vòng 365 ngày với hour patterns

**Sau:**
- **CHỈ** hard-coded test accounts có print jobs
- Test accounts: **5-15 jobs** mỗi account (random)
- **90% completed status**, 10% các status khác:
  - 90% `'completed'`
  - 2% `'pending'`
  - 2% `'printing'`
  - 2% `'failed'`
  - 2% `'cancelled'`
  - 2% `'pending_payment'`
- **Dates trong quá khứ**: Phân bố ngẫu nhiên trong **6 tháng gần nhất** (180 days ago to now)
- `uploaded_file.created_at` cũng được set trong quá khứ

**Hard-coded test accounts (giống như deposits):**
- `student.test@edu.vn`
- `phandienmanhthienk16@siu.edu.vn`
- `leanhtuank16@siu.edu.vn` (có print jobs nhưng không có deposits/payments)
- `nguyenhongbaongock16@siu.edu.vn`
- `phanthanhthaituank16@siu.edu.vn`
- `lengocdangkhoak16@siu.edu.vn`
- `lyhieuvyk17@siu.edu.vn`

---

### 3. HẠN CHẾ STAFF CREATION

#### 3.1. Printer Creation

**Trước:**
- `created_by` được chọn ngẫu nhiên từ tất cả staff members

**Sau:**
- `created_by` **CHỈ** sử dụng test staff (`staff.test@edu.vn`)
- Tất cả printers được tạo bởi test staff account

**Code changes:**
```python
# Trước
creator_staff = random.choice(self.staff) if self.staff else None

# Sau
test_staff_user = next((u for u in self.users if u.get('email') == 'staff.test@edu.vn'), None)
creator_staff = None
if test_staff_user and self.staff:
    creator_staff = next((s for s in self.staff if s.get('user_id') == test_staff_user['user_id']), None)
```

---

### 4. THAY ĐỔI TRONG DATA GENERATION SCRIPT

#### 4.1. File: `pmtm_database/pipeline/generate.py`

**Function: `generate_deposits()`**
- Thêm logic để generate `deposit_code` unique
- Thêm logic để set `expired_at` dựa trên status
- Thêm logic để set `cancellation_reason` cho cancelled deposits
- Thay đổi từ 20 deposits → 5-9 deposits cho test accounts
- Loại bỏ generation cho non-test accounts

**Function: `generate_print_jobs()`**
- Thay đổi từ 20 jobs → 5-15 jobs cho test accounts
- Loại bỏ generation cho non-test accounts
- Thay đổi status distribution: 90% completed
- Thay đổi date range: 180 days (6 months) thay vì 365 days
- Set `uploaded_file.created_at` trong quá khứ

**Function: `generate_printer_infrastructure()`**
- Thay đổi `creator_staff` selection: chỉ test staff

---

## MIGRATION NOTES

### Breaking Changes

1. **Deposit Table Schema:**
   - Cần thêm 3 trường mới: `deposit_code`, `expired_at`, `cancellation_reason`
   - Cần update CHECK constraint cho `payment_status`
   - Cần tạo index cho `deposit_code`

2. **Data Generation:**
   - Chỉ test accounts có deposits và print jobs
   - Số lượng deposits/jobs giảm đáng kể
   - Dates chỉ trong 6 tháng gần nhất

### Migration Steps

1. **Update Schema:**
   ```sql
   -- Backup existing data
   SELECT * INTO deposit_backup FROM deposit;
   
   -- Add new columns
   ALTER TABLE deposit ADD deposit_code VARCHAR(8) NULL;
   ALTER TABLE deposit ADD expired_at DATETIME NULL;
   ALTER TABLE deposit ADD cancellation_reason NVARCHAR(500) NULL;
   
   -- Generate deposit codes for existing records
   -- (Cần script để generate unique codes)
   
   -- Make deposit_code NOT NULL after populating
   ALTER TABLE deposit ALTER COLUMN deposit_code VARCHAR(8) NOT NULL;
   ALTER TABLE deposit ADD CONSTRAINT UQ_deposit_code UNIQUE (deposit_code);
   
   -- Update CHECK constraint
   ALTER TABLE deposit DROP CONSTRAINT [old_constraint_name];
   ALTER TABLE deposit ADD CONSTRAINT chk_deposit_payment_status 
       CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded', 'expired', 'cancelled'));
   
   -- Create index
   CREATE INDEX idx_deposit_code ON deposit (deposit_code);
   ```

2. **Regenerate Data:**
   - Chạy lại `generate.py` để tạo data mới với restrictions
   - Xóa data cũ nếu cần (deposits, print_jobs từ non-test accounts)

---

## TESTING NOTES

### Test Cases

1. **Deposit Schema:**
   - ✅ Verify `deposit_code` is unique and 8 characters
   - ✅ Verify `expired_at` is set correctly for pending/expired deposits
   - ✅ Verify `cancellation_reason` is set for cancelled deposits
   - ✅ Verify CHECK constraint allows all new status values

2. **Data Generation:**
   - ✅ Verify only test accounts have deposits (5-9 each)
   - ✅ Verify only test accounts have print jobs (5-15 each)
   - ✅ Verify 90% of print jobs are completed
   - ✅ Verify all dates are in the past (last 6 months)
   - ✅ Verify printers are created by test staff only

3. **Data Integrity:**
   - ✅ Verify deposit codes are unique
   - ✅ Verify expired_at is NULL for completed/failed deposits
   - ✅ Verify cancellation_reason is NULL for non-cancelled deposits

---

## IMPACT ASSESSMENT

### High Impact
- **Data Volume:** Giảm đáng kể số lượng deposits và print jobs (chỉ test accounts)
- **Schema Changes:** Cần migration cho deposit table

### Medium Impact
- **Date Ranges:** Tất cả dates trong 6 tháng gần nhất (thay vì 1-2 năm)
- **Status Distribution:** 90% completed print jobs (thay vì distribution theo spec)

### Low Impact
- **Staff Assignment:** Chỉ ảnh hưởng printer creation (không ảnh hưởng business logic)

---

## ROLLBACK PLAN

Nếu cần rollback:

1. **Schema Rollback:**
   ```sql
   -- Remove new columns
   ALTER TABLE deposit DROP COLUMN deposit_code;
   ALTER TABLE deposit DROP COLUMN expired_at;
   ALTER TABLE deposit DROP COLUMN cancellation_reason;
   
   -- Restore old CHECK constraint
   ALTER TABLE deposit DROP CONSTRAINT chk_deposit_payment_status;
   ALTER TABLE deposit ADD CONSTRAINT chk_deposit_payment_status 
       CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded'));
   
   -- Drop index
   DROP INDEX idx_deposit_code ON deposit;
   ```

2. **Data Rollback:**
   - Restore từ backup nếu có
   - Hoặc regenerate với code cũ

---

## RELATED CHANGELOGS

- **Changelog 6:** VND Currency and Schema Updates
- **Changelog 5:** Page Count and Print Tracking
- **Changelog 4:** Color Mode Multiplier

---

## NOTES

- Tất cả changes đã được test và verified
- Data generation script đã được cập nhật và tested
- Schema changes đã được applied trong `design.sql`
- Ready for production deployment

