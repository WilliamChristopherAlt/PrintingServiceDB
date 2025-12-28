# Hệ Thống Dịch Vụ In Thông Minh Cho Sinh Viên SIU (SSPS)
## Bài Thuyết Trình Dự Án

---

## Slide 1: Tổng Quan Dự Án

**Hệ Thống Dịch Vụ In Thông Minh Cho Sinh Viên SIU (SSPS)**

Hệ thống dịch vụ in thông minh toàn diện được thiết kế cho sinh viên tại Đại học Quốc tế Sài Gòn (Saigon International University - SIU). Hệ thống cho phép sinh viên in tài liệu tại nhiều địa điểm trong khuôn viên trường thông qua ứng dụng web và di động.

**Điểm Nổi Bật:**
- Ứng dụng full-stack với kiến trúc hiện đại
- Theo dõi công việc in và quản lý hàng đợi theo thời gian thực
- Hệ thống thanh toán tích hợp với quản lý số dư
- Dashboard quản trị toàn diện cho quản lý hệ thống
- Hỗ trợ đa ngôn ngữ (Tiếng Việt & Tiếng Anh)

---

## Slide 2: Các Chức Năng Chính

**Hệ thống hỗ trợ các chức năng sau:**

**Cho Sinh Viên:**
- Đăng nhập và xác thực
- Tải lên tài liệu (PDF, DOCX, Office files)
- Chọn máy in từ danh sách có sẵn
- Cấu hình tùy chọn in (kích thước giấy, chế độ màu, số bản, một/hai mặt)
- Xem giá dự kiến trước khi in
- Thanh toán bằng số dư hoặc QR code
- Theo dõi tiến trình in thời gian thực
- Xem lịch sử in và giao dịch
- Nạp tiền vào tài khoản với gói khuyến mãi
- Nhận thưởng học kỳ tự động
- Hủy công việc in và nhận hoàn tiền

**Cho Nhân Viên (SPSO):**
- Quản lý máy in (thêm, bật, tắt, cập nhật)
- Cấu hình hệ thống (giá cả, loại file được phép, thưởng học kỳ)
- Xem báo cáo sử dụng (hàng tháng, hàng năm)
- Xem lịch sử in của tất cả sinh viên
- Quản lý sinh viên và tài khoản
- Xem nhật ký hệ thống và máy in
- Quản lý gói khuyến mãi nạp tiền

**Tự Động:**
- Tính toán số dư từ các giao dịch
- Tạo báo cáo tự động
- Ghi nhận tất cả hành động in
- Cập nhật trạng thái công việc in
- Gửi thông báo thời gian thực

---

## Slide 3: Bối Cảnh & Stakeholders

**Bối Cảnh:**
Hệ thống hoạt động trong môi trường đại học nơi sinh viên thường xuyên cần in các tài liệu học thuật (bài tập, báo cáo, luận văn, tài liệu tham khảo). Hệ thống quản lý mạng lưới máy in phân tán tại nhiều tòa nhà và phòng học trong khuôn viên, cung cấp truy cập thuận tiện thông qua ứng dụng web và di động.

**Stakeholders:**
1. **Sinh viên** - Người dùng chính, tải lên tài liệu, chọn máy in, cấu hình cài đặt in và quản lý số dư in
2. **SPSO (Nhân viên Dịch vụ In Sinh viên)** - Nhân viên quản lý máy in, cấu hình hệ thống, xem báo cáo và giám sát việc sử dụng hệ thống
3. **Ban Giám hiệu** - Người ra quyết định cần báo cáo sử dụng, dữ liệu doanh thu và chỉ số hiệu quả hoạt động

---

## Slide 4: Tổng Quan Kiến Trúc Hệ Thống

**Thiết Kế Kiến Trúc Phân Lớp:**

**Lớp Presentation:**
- Frontend Next.js 14 (React với TypeScript)
- Ứng dụng web responsive với hỗ trợ di động
- Cập nhật thời gian thực qua WebSocket
- Đa ngôn ngữ (i18n)

**Lớp Business Logic:**
- REST API Spring Boot 3.3.6
- Kiến trúc hướng dịch vụ
- Quản lý giao dịch
- Thực thi quy tắc nghiệp vụ

**Lớp Data Access:**
- JPA/Hibernate ORM
- Repository pattern
- Database views cho các truy vấn phức tạp
- Tối ưu với indexes

**Lưu Trữ Dữ Liệu:**
- Cơ sở dữ liệu Azure SQL Server
- Supabase Storage cho quản lý file
- Lưu trữ file và metadata

---

## Slide 4.5: Sơ Đồ Kiến Trúc Tổng Thể

**[PLACEHOLDER: Chèn sơ đồ kiến trúc tổng thể tại đây]**

**Mô tả:**
- Sơ đồ hiển thị các thành phần chính của hệ thống
- Luồng dữ liệu giữa các lớp
- Tích hợp với các dịch vụ bên ngoài
- Kết nối giữa frontend, backend và database

---

## Slide 5: Schema Cơ Sở Dữ Liệu - Các Entity Chính

**Thiết Kế Cơ Sở Dữ Liệu:**
- **43+ bảng** với các mối quan hệ toàn diện
- **Khóa chính dạng UUID** để mở rộng
- **Schema chuẩn hóa** tuân theo nguyên tắc 3NF
- **Views** cho các truy vấn báo cáo phức tạp

**Các Nhóm Entity Chính:**

1. **Quản Lý Người Dùng:**
   - `user`, `student`, `staff`
   - Xác thực: `refresh_token`, `password_reset_token`

2. **Cơ Cấu Học Thuật:**
   - `faculty`, `department`, `major`, `class`, `academic_year`, `semester`

3. **Quản Lý Vị Trí:**
   - `building`, `floor`, `room` (hỗ trợ sơ đồ tầng)

4. **Quản Lý Máy In:**
   - `brand`, `printer_model`, `printer_physical`
   - Theo dõi trạng thái và nhật ký bảo trì

---

## Slide 6: Schema Cơ Sở Dữ Liệu - Logic Nghiệp Vụ

**Quản Lý Công Việc In:**
- `uploaded_file` - Lưu trữ tài liệu với số trang
- `print_job` - Thực thể công việc in cốt lõi với giá cả
- `print_job_page` - Theo dõi từng trang cho tiến trình

**Quản Lý Tài Chính:**
- `deposit` - Giao dịch nạp tiền với gói khuyến mãi
- `payment` - Thanh toán công việc in
- `student_wallet_ledger` - Sổ cái trung tâm cho tất cả giao dịch
- `semester_bonus` - Tín dụng tự động mỗi học kỳ
- `refund_print_job` - Hoàn tiền hủy bỏ

**Cấu Hình Giá:**
- `page_size_price` - Giá cơ bản theo kích thước giấy
- `color_mode_price` - Hệ số nhân chế độ màu
- `page_discount_package` - Giảm giá khối lượng

**Cấu Hình Hệ Thống:**
- `system_configuration` - Cài đặt dạng key-value
- `permitted_file_type` - Định dạng file được phép

---

## Slide 7: Kiến Trúc Backend - Spring Boot API

**Công Nghệ Sử Dụng:**
- **Framework:** Spring Boot 3.3.6
- **Phiên Bản Java:** 17
- **ORM:** Hibernate 6.5.3 với JPA
- **Bảo Mật:** Spring Security với xác thực JWT
- **Tài Liệu:** OpenAPI 3 (Swagger UI)
- **Thời Gian Thực:** WebSocket với giao thức STOMP

**Tính Năng Chính:**
- Thiết kế RESTful API với phản hồi chuẩn hóa
- Xử lý lỗi toàn diện
- Quản lý giao dịch
- Tác vụ lên lịch cho các quy trình tự động
- Hỗ trợ WebSocket cho cập nhật thời gian thực

**Cấu Trúc Package:**
- `controller` - 30+ REST controllers
- `service` - 60+ dịch vụ logic nghiệp vụ
- `repository` - 35+ repository truy cập dữ liệu
- `entity` - 43+ JPA entities
- `dto` - 110+ đối tượng chuyển dữ liệu

---

## Slide 8: Backend - Các Dịch Vụ Chính

1. **Dịch Vụ Công Việc In:**
   - Tạo công việc và quản lý hàng đợi
   - Theo dõi tiến trình thời gian thực
   - Cập nhật trạng thái (queued → printing → completed)
   - Tính giá với giảm giá

2. **Dịch Vụ Thanh Toán:**
   - Kiểm tra và trừ số dư
   - Xử lý thanh toán (số dư/mã QR)
   - Xử lý hoàn tiền khi hủy
   - Tích hợp với cổng thanh toán SePay

3. **Dịch Vụ Quản Lý File:**
   - Tải tài liệu lên Supabase Storage
   - Tính số trang (PDF, DOCX, Office files)
   - Xác thực và kiểm tra loại file

4. **Dịch Vụ Thông Báo:**
   - Thông báo thời gian thực qua WebSocket
   - Thông báo email cho các sự kiện quan trọng
   - Hệ thống thông báo trong ứng dụng

5. **Dịch Vụ Báo Cáo:**
   - Tạo báo cáo hàng tháng và hàng năm
   - Thống kê sử dụng máy in
   - Báo cáo hoạt động sinh viên

---

## Slide 9: Kiến Trúc Frontend - Ứng Dụng Next.js

**Công Nghệ Sử Dụng:**
- **Framework:** Next.js 14 (App Router)
- **Ngôn Ngữ:** TypeScript (chế độ strict)
- **Styling:** TailwindCSS
- **Quản Lý State:** Zustand (client) + TanStack Query (server)
- **Form:** React Hook Form + Zod validation
- **Đa Ngôn Ngữ:** next-intl (vi, en)
- **Đồ Họa 3D:** Three.js cho hiển thị máy in

**Tính Năng Chính:**
- Server-side rendering (SSR) và static generation
- Cập nhật thời gian thực qua WebSocket
- Thiết kế responsive (mobile-first)
- Hỗ trợ theme tối/sáng
- Khả năng Progressive Web App (PWA)

**Cấu Trúc Dự Án:**
- `app/[locale]/` - Routes đã địa phương hóa
- `components/` - Các component UI tái sử dụng
- `lib/api/` - API client và services
- `lib/stores/` - Quản lý state
- `locales/` - File dịch thuật

---

## Slide 10: Frontend - Tính Năng Chính

**Giao Diện Sinh Viên:**
- Tải tài liệu với kéo thả
- Chọn máy in tương tác với bản đồ tầng
- Cấu hình công việc in thời gian thực
- Tính giá trực tiếp
- Theo dõi tiến trình công việc in
- Lịch sử giao dịch và quản lý số dư
- Wizard nhiều bước cho gửi in

**Giao Diện Nhân Viên:**
- Dashboard toàn diện với phân tích
- Quản lý máy in (thêm, bật, tắt)
- Quản lý cấu hình hệ thống
- Tạo và xem báo cáo
- Quản lý sinh viên
- Nhật ký hệ thống và audit trails

**Tính Năng Chung:**
- Hỗ trợ đa ngôn ngữ (Tiếng Việt/Tiếng Anh)
- Thiết kế responsive cho mọi thiết bị
- Thông báo thời gian thực
- Tùy chỉnh theme
- Tích hợp trình phát nhạc

---

## Slide 11: Quy Trình Công Việc In

**Quy Trình 5 Bước:**

1. **Tải Tài Liệu (20%)**
   - Tải file lên Supabase Storage
   - Tính số trang tự động
   - Xác thực file

2. **Chọn Máy In (40%)**
   - Duyệt máy in có sẵn theo vị trí
   - Xem trạng thái hàng đợi thời gian thực
   - Kiểm tra khả năng máy in

3. **Cấu Hình Cài Đặt (60%)**
   - Chọn kích thước giấy (A4, A3, A5)
   - Chế độ màu (Đen trắng, Xám, Màu)
   - Tùy chọn in (số bản, hướng, mặt)
   - Tính giá thời gian thực

4. **Xem Lại & Xác Nhận (80%)**
   - Xem lại tất cả cài đặt
   - Kiểm tra số dư và giá
   - Xác nhận cuối cùng

5. **Thanh Toán & Gửi (100%)**
   - Trừ số dư hoặc thanh toán QR
   - Tạo công việc in
   - Vào hàng đợi

---

## Slide 12: Hệ Thống Tính Giá

**Công Thức Tính Giá:**
```
Tổng Giá = (Tổng Trang × Giá Cơ Bản × Hệ Số Màu) × (1 - Giảm Giá)
```

**Thành Phần:**
1. **Giá Cơ Bản:** Cấu hình theo kích thước giấy (A4, A3, A5)
2. **Hệ Số Màu:**
   - Đen Trắng: 0.8x
   - Xám: 1.0x
   - Màu: 2.5x
3. **Giảm Giá Khối Lượng:** Giảm giá theo tầng dựa trên số trang
   - 10+ trang: giảm 5%
   - 20+ trang: giảm 10%
   - 50+ trang: giảm 15%

**Tính Năng:**
- Bảo tồn giá lịch sử (giá được lưu trong print_job)
- Tính giá thời gian thực
- Áp dụng giảm giá tự động
- Quy tắc A3 = 2× A4

---

## Slide 13: Hệ Thống Quản Lý Tài Chính

**Triển Khai Ledger Pattern:**
- Bảng `student_wallet_ledger` trung tâm
- Tất cả giao dịch tài chính được ghi lại dưới dạng ledger entries
- Audit trail hoàn chỉnh
- Tính số dư hiệu quả

**Các Loại Giao Dịch:**
1. **Nạp Tiền:** Nạp tiền với gói khuyến mãi
2. **Thưởng Học Kỳ:** Tín dụng tự động mỗi học kỳ
3. **Thanh Toán:** Phí công việc in
4. **Hoàn Tiền:** Hoàn tiền hủy bỏ (tỷ lệ với trang chưa in)

**Tính Số Dư:**
- Tính động từ ledger entries
- Cập nhật số dư thời gian thực
- Không lưu số dư (tránh không nhất quán)
- Truy vấn số dư dựa trên view để hiệu suất

**Phương Thức Thanh Toán:**
- Thanh toán bằng số dư trong ứng dụng
- Thanh toán mã QR (tích hợp SePay)
- Thanh toán hỗn hợp (số dư + trực tiếp)

---

## Slide 14: Tính Năng Thời Gian Thực

**Tích Hợp WebSocket:**
- Giao thức STOMP qua WebSocket
- Cập nhật tiến trình công việc in thời gian thực
- Cập nhật trạng thái hàng đợi trực tiếp
- Giao thông báo tức thì

**Cập Nhật Thời Gian Thực:**
1. **Tiến Trình Công Việc In:**
   - Phần trăm hoàn thành
   - Trang đã in / tổng trang
   - Thời gian còn lại ước tính
   - Thay đổi trạng thái (queued → printing → completed)

2. **Quản Lý Hàng Đợi:**
   - Số lượng hàng đợi trực tiếp
   - Vị trí trong hàng đợi
   - Thời gian chờ ước tính

3. **Thông Báo:**
   - Xác nhận thanh toán
   - Hoàn thành công việc in
   - Thông báo hệ thống

**Cơ Chế Dự Phòng:**
- Polling API cho client không hỗ trợ WebSocket
- Khoảng thời gian cập nhật có thể cấu hình

---

## Slide 15: Tích Hợp Hệ Thống

**Các Dịch Vụ Bên Ngoài:**

1. **Supabase Storage:**
   - Lưu trữ file tài liệu
   - Hình ảnh model máy in (2D/3D)
   - Truy cập file an toàn

2. **Cổng Thanh Toán SePay:**
   - Tạo mã QR thanh toán
   - Xử lý webhook cho xác nhận thanh toán
   - Ghi log giao dịch

3. **ConvertAPI:**
   - Chuyển đổi tài liệu (DOCX → PDF)
   - Tính số trang cho Office files
   - Xác thực định dạng file

4. **Dịch Vụ Email (SMTP):**
   - Email đặt lại mật khẩu
   - Xác nhận giao dịch
   - Thông báo hệ thống

---

## Slide 16: Quy Trình Phát Triển

**Các Giai Đoạn Dự Án:**

1. **Thu Thập Yêu Cầu:**
   - Phân tích miền
   - Xác định các bên liên quan
   - Yêu cầu chức năng và phi chức năng
   - Mô hình hóa use case

2. **Mô Hình Hóa Hệ Thống:**
   - Sơ đồ hoạt động với swimlanes
   - Sơ đồ tuần tự
   - Sơ đồ lớp
   - Sơ đồ thành phần

3. **Thiết Kế Kiến Trúc:**
   - Thiết kế kiến trúc phân lớp
   - Sơ đồ thành phần
   - Thiết kế API
   - Thiết kế schema cơ sở dữ liệu

4. **Triển Khai - Sprint 1:**
   - Thiết lập repository (GitHub)
   - Tổ chức tài liệu
   - Wireframe UI (MVP 1)
   - Kiểm thử khả năng sử dụng

5. **Triển Khai - Sprint 2:**
   - Phát triển MVP 2
   - Triển khai full-stack
   - Kiểm thử tích hợp
   - Chuẩn bị triển khai

---

## Slide 17: Kiểm Thử & Đảm Bảo Chất Lượng

**Chiến Lược Kiểm Thử:**

1. **Kiểm Thử Đơn Vị:**
   - Kiểm thử lớp service
   - Kiểm thử repository
   - Kiểm thử hàm tiện ích

2. **Kiểm Thử Tích Hợp:**
   - Kiểm thử endpoint API
   - Kiểm thử tích hợp cơ sở dữ liệu
   - Mock dịch vụ bên ngoài

3. **Kiểm Thử Khả Năng Sử Dụng:**
   - Kiểm thử giao diện người dùng
   - Đánh giá trải nghiệm người dùng
   - Thu thập và phân tích phản hồi

**Chất Lượng Code:**
- **ESLint** cho JavaScript/TypeScript
- **Prettier** cho định dạng code
- **SonarQube** cho phân tích code
- **TypeScript strict mode** cho an toàn kiểu
- **Husky** cho pre-commit hooks

**Tài Liệu:**
- Tài liệu API toàn diện (Swagger)
- Hướng dẫn nhà phát triển
- Tài liệu kiến trúc hệ thống
- Tài liệu schema cơ sở dữ liệu

---

## Slide 18: Triển Khai & DevOps

**Kiến Trúc Triển Khai:**

**Backend:**
- **Nền Tảng:** Heroku
- **Cơ Sở Dữ Liệu:** Azure SQL Server
- **CI/CD:** GitHub Actions
- **Build:** Maven
- **Giám Sát:** Metrics và logs Heroku

**Frontend:**
- **Nền Tảng:** Heroku (hoặc Vercel)
- **Build:** Next.js production build
- **CI/CD:** GitHub Actions

**Pipeline CI/CD:**
1. Push code lên GitHub
2. Kiểm thử tự động
3. Build và đóng gói
4. Triển khai lên staging/production
5. Health checks và giám sát

**Quản Lý Cấu Hình:**
- Biến môi trường cho dữ liệu nhạy cảm
- Cấu hình riêng cho dev/staging/prod
- Script migration cơ sở dữ liệu
- Kiểm soát phiên bản cho tất cả cấu hình

---

## Slide 19: Thách Thức & Giải Pháp

**Các Thách Thức Kỹ Thuật Chính:**

1. **Theo Dõi Tiến Trình Thời Gian Thực**
   Do không có tích hợp API máy in trực tiếp, hệ thống sử dụng mô phỏng tiến trình dựa trên thời gian và tốc độ in ước tính. Giải pháp được triển khai thông qua các tác vụ lên lịch với tỷ lệ có thể cấu hình.

2. **Tính Toàn Vẹn Giao Dịch Tài Chính**
   Để đảm bảo tính toán số dư chính xác, hệ thống áp dụng Ledger pattern với nguồn sự thật duy nhất. Tất cả giao dịch được ghi lại trong bảng ledger trung tâm, tạo ra lịch sử giao dịch đầy đủ và đáng tin cậy.

3. **Hỗ Trợ Định Dạng File Đa Dạng**
   Hệ thống cần xử lý nhiều định dạng file khác nhau (PDF, DOCX, Office files). Giải pháp kết hợp ConvertAPI cho chuyển đổi tài liệu và PDFBox cho xử lý PDF, tự động tính số trang cho mọi loại file.

4. **Địa Phương Hóa Đa Ngôn Ngữ**
   Việc hỗ trợ nhiều ngôn ngữ cho UI và nội dung được giải quyết bằng next-intl với các file dịch thuật. Hệ thống sử dụng routing dựa trên locale và tải nội dung động theo ngôn ngữ người dùng chọn.

---

## Slide 20: Bài Học Kinh Nghiệm

**Hiểu Biết Phát Triển:**

1. **Thiết Kế Cơ Sở Dữ Liệu:**
   - Ledger pattern cung cấp audit trail xuất sắc
   - Views đơn giản hóa các truy vấn báo cáo phức tạp
   - Indexing phù hợp quan trọng cho hiệu suất
   - Bảo tồn dữ liệu lịch sử quan trọng cho giá cả

2. **Kiến Trúc:**
   - Kiến trúc phân lớp cho phép bảo trì
   - Tách biệt mối quan tâm cải thiện khả năng kiểm thử
   - Thiết kế API-first tạo điều kiện phát triển frontend/backend song song

3. **Trải Nghiệm Người Dùng:**
   - Cập nhật thời gian thực cải thiện đáng kể UX
   - Wizard nhiều bước giảm lỗi người dùng
   - Phân tích giá rõ ràng xây dựng niềm tin
   - Thiết kế responsive cần thiết cho người dùng di động

4. **Quản Lý Dự Án:**
   - Tài liệu toàn diện tiết kiệm thời gian
   - Kiểm soát phiên bản cần thiết cho cộng tác nhóm
   - Kiểm thử thường xuyên ngăn ngừa vấn đề production
   - Kiểm thử khả năng sử dụng tiết lộ cải thiện UX

5. **Kỹ Năng Kỹ Thuật:**
   - Phát triển full-stack yêu cầu kiến thức rộng
   - Hiểu logic nghiệp vụ là quan trọng
   - Tích hợp với dịch vụ bên ngoài thêm độ phức tạp
   - Tối ưu hiệu suất là quá trình liên tục

---

## Slide 21: Cải Tiến Tương Lai & Kết Luận

**Cải Tiến Tương Lai:**

1. **Ứng Dụng Di Động:**
   - Ứng dụng iOS và Android gốc
   - Push notifications
   - Khả năng offline

2. **Tính Năng Nâng Cao:**
   - Lên lịch công việc in
   - Template tài liệu
   - In cộng tác
   - Cải thiện xem trước in

3. **Phân Tích:**
   - Dashboard báo cáo nâng cao
   - Phân tích dự đoán
   - Phân tích mẫu sử dụng
   - Khuyến nghị tối ưu chi phí

4. **Tích Hợp:**
   - Cổng thanh toán bổ sung
   - Tích hợp Hệ thống Quản lý Học tập (LMS)
   - Tích hợp hệ thống thông tin sinh viên