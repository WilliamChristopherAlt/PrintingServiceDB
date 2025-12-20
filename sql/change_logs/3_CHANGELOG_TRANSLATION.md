# NHẬT KÝ THAY ĐỔI: HỆ THỐNG ĐA NGÔN NGỮ (MULTI-LANGUAGE SUPPORT)
## Smart Printing Service System (SSPS)

---

## TỔNG QUAN
Tài liệu này ghi lại việc triển khai hệ thống đa ngôn ngữ để hỗ trợ dịch các cột name và description sang nhiều ngôn ngữ khác nhau. Tất cả các cột name/description hiện tại được giả định là tiếng Anh, và bảng `name_translation` lưu trữ các bản dịch cho các ngôn ngữ khác (hiện tại hỗ trợ tiếng Việt).

---

## CÁC THAY ĐỔI CHI TIẾT

### 1. BẢNG `language` - QUẢN LÝ NGÔN NGỮ

#### Thay đổi:
- **THÊM bảng:** `language`
- **Các cột:**
  - `language_id` (UNIQUEIDENTIFIER, PK)
  - `language_name` (NVARCHAR(50), NOT NULL, UNIQUE) – Tên ngôn ngữ (ví dụ: 'English', 'Vietnamese')
  - `acronym` (VARCHAR(10), NOT NULL, UNIQUE) – Mã ngôn ngữ (ví dụ: 'en', 'vi')
  - `created_at` (DATETIME)
- **THÊM index:**
  - `idx_language_acronym` trên `acronym`

#### Lý do:
Tạo bảng trung tâm để quản lý các ngôn ngữ được hỗ trợ trong hệ thống:
- Cho phép mở rộng dễ dàng sang các ngôn ngữ khác trong tương lai
- Cung cấp cách tham chiếu chuẩn đến ngôn ngữ thông qua `acronym` (ISO 639-1)
- Tách biệt việc quản lý ngôn ngữ khỏi logic dịch thuật

#### Dữ liệu mặc định:
- English (en)
- Vietnamese (vi)

---

### 2. BẢNG `name_translation` - LƯU TRỮ BẢN DỊCH

#### Thay đổi:
- **THÊM bảng:** `name_translation`
- **Các cột:**
  - `translation_id` (UNIQUEIDENTIFIER, PK)
  - `table_name` (VARCHAR(100), NOT NULL) – Tên bảng chứa cột cần dịch (ví dụ: 'faculty', 'department')
  - `entry_id` (UNIQUEIDENTIFIER, NOT NULL) – ID của record trong bảng nguồn
  - `column_name` (VARCHAR(100), NOT NULL) – Tên cột cần dịch (ví dụ: 'faculty_name', 'description')
  - `language_id` (UNIQUEIDENTIFIER, NOT NULL, FK → `language.language_id`) – Ngôn ngữ của bản dịch
  - `translation` (NVARCHAR(500), NOT NULL) – Nội dung bản dịch
  - `created_at` (DATETIME)
- **THÊM indexes:**
  - `idx_translation_table_entry` trên `(table_name, entry_id)`
  - `idx_translation_column` trên `column_name`
  - `idx_translation_language` trên `language_id`
  - `idx_translation_table_column` trên `(table_name, column_name)`

#### Lý do:
Triển khai pattern dịch thuật linh hoạt cho các cột name và description:
- **Không thay đổi cấu trúc bảng hiện có:** Tất cả các cột name/description giữ nguyên, được giả định là tiếng Anh
- **Hỗ trợ đa ngôn ngữ:** Lưu trữ bản dịch cho từng record và từng cột riêng biệt
- **Mở rộng dễ dàng:** Thêm ngôn ngữ mới chỉ cần thêm record vào `language` và tạo translations

#### Các bảng và cột được hỗ trợ dịch:
1. **`faculty`**: `faculty_name`, `description`
2. **`department`**: `department_name`, `description`
3. **`major`**: `major_name`, `description`
4. **`building`**: `campus_name`
5. **`room`**: `room_name` (chỉ dịch các tên có ý nghĩa, bỏ qua các mã như "101", "F1R01")
6. **`brand`**: `brand_name`
7. **`printer_model`**: `model_name`, `description`
8. **`semester`**: `term_name` (chỉ dịch: fall, spring, summer)
9. **`deposit_bonus_package`**: `package_name`, `description`
10. **`semester_bonus`**: `description`
11. **`color_mode`**: `color_mode_name`
12. **`page_discount_package`**: `package_name`, `description`
13. **`fund_source`**: `fund_source_name`, `description`
14. **`supplier_paper_purchase`**: `supplier_name`

#### Các bảng KHÔNG được dịch (có lý do):
- **`class`**: `class_name` - Không dịch vì là mã lớp (ví dụ: "CS0101")
- **`page_size`**: `size_name` - Không dịch vì là tên chuẩn quốc tế (A3, A4, A5)

---

## CÁCH SỬ DỤNG

### Truy vấn bản dịch tiếng Việt:

```sql
-- Lấy tên khoa bằng tiếng Việt
SELECT 
    f.faculty_id,
    f.faculty_name AS name_en,
    nt.translation AS name_vi
FROM faculty f
LEFT JOIN name_translation nt ON nt.table_name = 'faculty' 
    AND nt.entry_id = f.faculty_id 
    AND nt.column_name = 'faculty_name'
    AND nt.language_id = (SELECT language_id FROM language WHERE acronym = 'vi')
WHERE f.faculty_id = @faculty_id;
```

### Thêm bản dịch mới:

```sql
-- Thêm bản dịch tiếng Việt cho tên khoa
INSERT INTO name_translation (translation_id, table_name, entry_id, column_name, language_id, translation, created_at)
VALUES (
    NEWID(),
    'faculty',
    @faculty_id,
    'faculty_name',
    (SELECT language_id FROM language WHERE acronym = 'vi'),
    N'Tên khoa bằng tiếng Việt',
    GETDATE()
);
```

### Thêm ngôn ngữ mới:

```sql
-- Thêm ngôn ngữ mới (ví dụ: tiếng Trung)
INSERT INTO language (language_id, language_name, acronym, created_at)
VALUES (NEWID(), 'Chinese', 'zh', GETDATE());
```

---

## TÁC ĐỘNG ĐẾN ỨNG DỤNG

### Khi hiển thị dữ liệu:
- Ứng dụng cần query bảng `name_translation` để lấy bản dịch theo ngôn ngữ người dùng chọn
- Nếu không có bản dịch, hiển thị giá trị từ cột gốc (tiếng Anh)
- Có thể tạo view hoặc stored procedure để đơn giản hóa việc lấy bản dịch

### Khi tạo/cập nhật dữ liệu:
- Khi tạo record mới trong các bảng có cột name/description, cần tạo translations tương ứng nếu cần
- Script `generate.py` đã được cập nhật để tự động tạo Vietnamese translations cho tất cả dữ liệu

### Khi thêm ngôn ngữ mới:
- Thêm record vào bảng `language`
- Tạo translations cho ngôn ngữ mới trong bảng `name_translation`
- Cập nhật logic ứng dụng để hỗ trợ ngôn ngữ mới

---

## CẤU TRÚC DỮ LIỆU

### Ví dụ dữ liệu trong `name_translation`:

| translation_id | table_name | entry_id | column_name | language_id | translation | created_at |
|----------------|------------|----------|-------------|-------------|-------------|------------|
| UUID-1 | faculty | UUID-F1 | faculty_name | UUID-VI | Khoa Công nghệ Thông tin | 2024-01-01 |
| UUID-2 | faculty | UUID-F1 | description | UUID-VI | Khoa đào tạo về CNTT | 2024-01-01 |
| UUID-3 | department | UUID-D1 | department_name | UUID-VI | Bộ môn Hệ thống Thông tin | 2024-01-01 |

---

## GHI CHÚ
- Bảng `language` và `name_translation` đã được thêm vào `design.sql`
- Script sinh dữ liệu (`generate.py`) đã được cập nhật để:
  - Tạo dữ liệu language (English, Vietnamese)
  - Tự động tạo Vietnamese translations cho các cột name/description có thể dịch
  - Chỉ tạo translations khi bản dịch khác với bản gốc và hoàn toàn bằng tiếng Việt
  - Bỏ qua translations cho các mã/codes (class_name, page_size) và các giá trị không thể dịch
- Diagram module "Cấu hình Hệ thống" đã được cập nhật để bao gồm 2 bảng mới
- Tất cả các cột name/description trong bảng gốc được giả định là tiếng Anh
- Vietnamese translations được tạo tự động trong quá trình generate data
- Chỉ các bản dịch hoàn toàn bằng tiếng Việt (không chứa từ tiếng Anh) mới được thêm vào bảng translation
- Các bản dịch giống với bản gốc sẽ không được thêm vào (tránh trùng lặp)

---

## CÁC BẢNG LIÊN QUAN

### Bảng được dịch:
- `faculty` → `faculty_name`, `description`
- `department` → `department_name`, `description`
- `major` → `major_name`, `description`
- `building` → `campus_name`
- `room` → `room_name` (chỉ dịch các tên có ý nghĩa, bỏ qua mã)
- `brand` → `brand_name`
- `printer_model` → `model_name`, `description`
- `semester` → `term_name` (chỉ dịch: fall, spring, summer)
- `deposit_bonus_package` → `package_name`, `description`
- `semester_bonus` → `description`
- `color_mode` → `color_mode_name`
- `page_discount_package` → `package_name`, `description`
- `fund_source` → `fund_source_name`, `description`
- `supplier_paper_purchase` → `supplier_name`

### Bảng KHÔNG được dịch (có lý do):
- `class` → `class_name` - Không dịch vì là mã lớp (ví dụ: "CS0101")
- `page_size` → `size_name` - Không dịch vì là tên chuẩn quốc tế (A3, A4, A5)

### Bảng không được dịch (không có cột name/description):
- `user` → `full_name` không được dịch (tên người dùng cá nhân)
- `student` → Không có cột name/description
- `staff` → Không có cột name/description
- `print_job` → Không có cột name/description
- Các bảng khác không có cột name/description cần dịch

