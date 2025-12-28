# NHẬT KÝ THAY ĐỔI: THÊM PAGE_COUNT VÀ THEO DÕI TRẠNG THÁI IN
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN
Thêm các cột mới để theo dõi số trang của file đã tải lên và trạng thái in của từng trang trong công việc in, cùng với các index để tối ưu hiệu suất truy vấn.

---

## THAY ĐỔI CHI TIẾT

### BẢNG `uploaded_file` - THÊM CỘT PAGE_COUNT

#### Thay đổi:
- **THÊM cột:** `page_count INT NOT NULL`
  - Lưu trữ số trang của file đã tải lên
  - Giúp theo dõi và quản lý số trang của tài liệu trước khi in

#### Lý do:
- Cần biết số trang của file để hiển thị thông tin cho người dùng
- Hỗ trợ tính toán chi phí và quản lý tài nguyên tốt hơn
- Cung cấp thông tin chi tiết về tài liệu trước khi tạo print job

---

### BẢNG `print_job_page` - THÊM THEO DÕI TRẠNG THÁI IN

#### Thay đổi:
- **THÊM cột:** `is_printed BIT DEFAULT 0 NOT NULL`
  - Đánh dấu trang đã được in hay chưa
  - Giá trị mặc định: 0 (chưa in)
  
- **THÊM cột:** `printed_at DATETIME2 NULL`
  - Thời điểm trang được in
  - NULL nếu trang chưa được in

#### Lý do:
- Cho phép theo dõi tiến độ in chi tiết từng trang
- Hỗ trợ tính toán chính xác số trang đã in khi job bị hủy giữa chừng
- Cung cấp thông tin chi tiết cho báo cáo và audit trail
- Hỗ trợ tính toán hoàn tiền chính xác khi hủy job

---

### INDEXES - TỐI ƯU HIỆU SUẤT

#### Thêm các index mới:

1. **`idx_print_job_page_job_printed`** trên `print_job_page(job_id, is_printed)`
   - Tối ưu truy vấn đếm số trang đã in/chưa in của một job
   - Hỗ trợ tính toán tiến độ in

2. **`idx_print_job_printer_status_created`** trên `print_job(printer_id, print_status, created_at)`
   - Tối ưu truy vấn tìm các job đang chờ hoặc đang in của một máy in
   - Hỗ trợ quản lý hàng đợi in

3. **`idx_print_job_status_start_time`** trên `print_job(print_status, start_time)`
   - Tối ưu truy vấn tìm các job đang in
   - Hỗ trợ theo dõi tiến độ in

#### Lý do:
- Cải thiện hiệu suất truy vấn cho các tác vụ thường xuyên:
  - Kiểm tra tiến độ in
  - Quản lý hàng đợi
  - Tính toán số trang đã in
- Giảm thời gian phản hồi cho các truy vấn phức tạp

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi tải file lên:
- **Cần tính toán số trang:** Ứng dụng cần đếm số trang của file khi tải lên và lưu vào `page_count`
- **Có thể sử dụng thư viện:** PDF (PyPDF2, pdfplumber), DOCX (python-docx), PPTX (python-pptx), Images (PIL/Pillow)

### Khi in trang:
- **Cập nhật trạng thái:** Khi một trang được in thành công, cần cập nhật:
  - `is_printed = 1`
  - `printed_at = GETDATE()` hoặc thời điểm in thực tế
- **Theo dõi tiến độ:** Có thể tính tiến độ in = (số trang có `is_printed = 1`) / (tổng số trang)

### Khi hủy job:
- **Tính toán chính xác:** Sử dụng `is_printed` để xác định số trang chưa in
- **Hoàn tiền:** Tính toán hoàn tiền dựa trên số trang có `is_printed = 0`

### Khi truy vấn:
- **Sử dụng index:** Các truy vấn về tiến độ in và hàng đợi sẽ nhanh hơn nhờ các index mới
- **Tối ưu query:** Sử dụng `is_printed` và `printed_at` trong WHERE và JOIN conditions

---

## MIGRATION

### Script migration:
- File: `sql/migrations/8_MIGRATION_ADD_PAGE_COUNT_AND_PRINT_TRACKING.sql`
- Bao gồm:
  1. Thêm cột `page_count` vào `uploaded_file`
  2. Cập nhật dữ liệu hiện có với ước tính số trang
  3. Thêm cột `is_printed` và `printed_at` vào `print_job_page`
  4. Cập nhật dữ liệu hiện có dựa trên trạng thái job
  5. Tạo các index mới

### Lưu ý khi migrate:
- Dữ liệu hiện có sẽ được ước tính số trang dựa trên file_type và file_size_kb
- Các job đã hoàn thành sẽ được đánh dấu tất cả trang đã in
- Các job đang in sẽ được đánh dấu một phần trang đã in

---

## NGÀY THỰC HIỆN
Thay đổi được thực hiện: 2025-12-20

---

## GHI CHÚ
- File `design.sql` đã được cập nhật với cấu trúc mới
- Script `generate.py` đã được cập nhật để sinh dữ liệu cho các cột mới
- Migration script đã được tạo và sẵn sàng sử dụng
- Các index mới sẽ cải thiện hiệu suất truy vấn đáng kể

