-- ============================================
-- HCMSIU Student Smart Printing Service (SSPS)
-- Database Schema
-- ============================================
-- SPSO = Student Printing Service Officer (staff managing the system)
-- ============================================

-- CREATE DATABASE IF NOT EXISTS printing_service_db;

USE printing_service_db;
GO

-- User Management Tables
-- ============================================

CREATE TABLE [user] (
    user_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name NVARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(10) NOT NULL CHECK (user_type IN ('student', 'staff')),
    phone_number VARCHAR(15),
    date_of_birth DATE,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female')),
    citizen_id VARCHAR(50),
    address VARCHAR(500),
    profile_picture VARCHAR(500),
    email_verified BIT DEFAULT 0,
    email_verification_code VARCHAR(255),
    account_status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended')),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    last_login_at DATETIME,
    is_active BIT DEFAULT 1
);
CREATE INDEX idx_user_type ON [user] (user_type);
CREATE INDEX idx_email ON [user] (email);
GO

-- Academic Structure Tables
-- ============================================

CREATE TABLE faculty (
    faculty_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_name NVARCHAR(100) NOT NULL UNIQUE,
    faculty_code VARCHAR(20) NOT NULL UNIQUE,
    description NVARCHAR(200),
    established_date DATE,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_faculty_code ON faculty (faculty_code);
GO

CREATE TABLE department (
    department_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_id UNIQUEIDENTIFIER NOT NULL,
    department_name NVARCHAR(100) NOT NULL,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    description NVARCHAR(200),
    established_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    UNIQUE (faculty_id, department_name)
);
CREATE INDEX idx_faculty ON department (faculty_id);
CREATE INDEX idx_department_code ON department (department_code);
GO

CREATE TABLE major (
    major_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    department_id UNIQUEIDENTIFIER NOT NULL,
    major_name NVARCHAR(100) NOT NULL,
    major_code VARCHAR(20) NOT NULL UNIQUE,
    degree_type VARCHAR(20) NOT NULL DEFAULT 'bachelor' CHECK (degree_type IN ('bachelor', 'master', 'doctorate')),
    duration_years INT NOT NULL DEFAULT 4,
    description NVARCHAR(200),
    established_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (department_id) REFERENCES department(department_id),
    UNIQUE (department_id, major_name)
);
CREATE INDEX idx_department ON major (department_id);
CREATE INDEX idx_major_code ON major (major_code);
GO

CREATE TABLE academic_year (
    academic_year_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    year_name NVARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_year_name ON academic_year (year_name);
CREATE INDEX idx_date_range ON academic_year (start_date, end_date);
GO

CREATE TABLE class (
    class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    major_id UNIQUEIDENTIFIER NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    class_name NVARCHAR(50) NOT NULL,
    class_code VARCHAR(20) NOT NULL UNIQUE,
    year_level INT NOT NULL, -- 1, 2, 3, 4 for bachelor; 1, 2 for master, etc.
    max_students INT DEFAULT 40,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (major_id) REFERENCES major(major_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id),
    UNIQUE (major_id, academic_year_id, class_name)
);
CREATE INDEX idx_major ON class (major_id);
CREATE INDEX idx_academic_year ON class (academic_year_id);
CREATE INDEX idx_class_code ON class (class_code);
GO

CREATE TABLE student (
    student_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    student_code VARCHAR(20) NOT NULL UNIQUE,
    class_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_date DATE,
    graduation_date DATE NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'graduated', 'suspended', 'withdrawn')),
    FOREIGN KEY (user_id) REFERENCES [user](user_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES class(class_id)
);
CREATE INDEX idx_student_code ON student (student_code);
CREATE INDEX idx_class ON student (class_id);
CREATE INDEX idx_status ON student (status);
GO

CREATE TABLE staff (
    staff_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    employee_code VARCHAR(20) NOT NULL UNIQUE,
    position VARCHAR(20) NOT NULL CHECK (position IN ('manager', 'technician', 'administrator', 'supervisor')),
    hire_date DATE,
    FOREIGN KEY (user_id) REFERENCES [user](user_id) ON DELETE CASCADE
);
CREATE INDEX idx_employee_code ON staff (employee_code);
GO

-- Page Size Table (must be created before printer_model)
-- ============================================

CREATE TABLE page_size (
    page_size_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    size_name NVARCHAR(20) NOT NULL UNIQUE,
    width_mm DECIMAL(6,2) NOT NULL,
    height_mm DECIMAL(6,2) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_size_name ON page_size (size_name);
GO

-- Building and Room Management Tables
-- ============================================

CREATE TABLE building (
    building_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_code VARCHAR(20) NOT NULL UNIQUE,
    address VARCHAR(255) NOT NULL,
    campus_name NVARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_building_code ON building (building_code);
CREATE INDEX idx_campus_name ON building (campus_name);
GO

CREATE TABLE floor (
    floor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_id UNIQUEIDENTIFIER NOT NULL,
    floor_number INT NOT NULL,
    file_url VARCHAR(500) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (building_id) REFERENCES building(building_id),
    UNIQUE (building_id, floor_number)
);
CREATE INDEX idx_building_floor ON floor (building_id);
CREATE INDEX idx_floor_number ON floor (floor_number);
GO

CREATE TABLE room (
    room_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    floor_id UNIQUEIDENTIFIER NOT NULL,
    room_code VARCHAR(20) NOT NULL,
    room_name NVARCHAR(100) NOT NULL,
    room_type NVARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (floor_id) REFERENCES floor(floor_id),
    UNIQUE (floor_id, room_code)
);
CREATE INDEX idx_floor_room ON room (floor_id);
CREATE INDEX idx_room_code ON room (room_code);
CREATE INDEX idx_room_type ON room (room_type);
GO

-- Printer Management Tables
-- ============================================

CREATE TABLE brand (
    brand_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    brand_name NVARCHAR(50) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50),
    website VARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE printer_model (
    model_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    brand_id UNIQUEIDENTIFIER NOT NULL,
    model_name NVARCHAR(50) NOT NULL,
    description NVARCHAR(200),
    max_paper_size_id UNIQUEIDENTIFIER NOT NULL,
    supports_color BIT DEFAULT 0,
    supports_duplex BIT DEFAULT 0,
    pages_per_second FLOAT,
    image_2d_url VARCHAR(255) NULL,
    image_3d_url VARCHAR(255) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (brand_id) REFERENCES brand(brand_id),
    FOREIGN KEY (max_paper_size_id) REFERENCES page_size(page_size_id),
    UNIQUE (brand_id, model_name)
);
CREATE INDEX idx_brand ON printer_model (brand_id);
CREATE INDEX idx_max_paper_size ON printer_model (max_paper_size_id);
GO

CREATE TABLE printer_physical (
    printer_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    model_id UNIQUEIDENTIFIER NOT NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    printer_pixel_coordinate VARCHAR(100) NULL, -- JSON: {"grid": [x, y], "pixel": [x, y]}
    is_enabled BIT DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'idle' CHECK (status IN ('unplugged', 'idle', 'printing', 'maintained')),
    printing_status VARCHAR(50) NULL CHECK (printing_status IN ('printing', 'paper_jam', 'out_of_paper', 'out_of_toner', 'low_toner', 'door_open', 'paper_tray_empty', 'network_error', 'offline', 'error')),
    installed_date DATE,
    last_maintenance_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (model_id) REFERENCES printer_model(model_id),
    FOREIGN KEY (room_id) REFERENCES room(room_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_model ON printer_physical (model_id);
CREATE INDEX idx_room ON printer_physical (room_id);
CREATE INDEX idx_enabled ON printer_physical (is_enabled);
CREATE INDEX idx_status ON printer_physical (status);
CREATE INDEX idx_printing_status ON printer_physical (printing_status);
GO

-- ============================================

-- Academic semesters (each academic year has Fall, Spring, Summer; academic year starts in September)
CREATE TABLE semester (
    semester_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    term_name NVARCHAR(10) NOT NULL CHECK (term_name IN ('fall', 'spring', 'summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    UNIQUE (academic_year_id, term_name),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);
CREATE INDEX idx_semester_academic_year ON semester (academic_year_id, term_name);
CREATE INDEX idx_semester_dates ON semester (start_date, end_date);
GO


-- ============================================
-- User Balance and Money Management Tables
-- ============================================

-- Note: User balance is calculated dynamically from deposits, semester bonuses, and payments
-- See view: student_balance_view for computed balance
GO

-- Deposit bonus package table - defines bonus tiers for deposits
CREATE TABLE deposit_bonus_package (
    package_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    amount_cap DECIMAL(10, 2) NOT NULL CHECK (amount_cap > 0), -- Minimum deposit amount to qualify
    bonus_percentage DECIMAL(5, 4) NOT NULL CHECK (bonus_percentage >= 0 AND bonus_percentage <= 1), -- Bonus percentage (0-1 range)
    package_name NVARCHAR(100),
    description NVARCHAR(200),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_deposit_bonus_package_amount ON deposit_bonus_package (amount_cap);
CREATE INDEX idx_deposit_bonus_package_active ON deposit_bonus_package (is_active);
GO

-- Deposit table - tracks each deposit/recharge transaction (real dollars to in-app currency)
CREATE TABLE deposit (
    deposit_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    deposit_amount DECIMAL(10, 2) NOT NULL CHECK (deposit_amount > 0), -- Real dollars deposited
    bonus_amount DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (bonus_amount >= 0), -- Bonus received
    total_credited DECIMAL(10, 2) NOT NULL CHECK (total_credited > 0), -- deposit_amount + bonus_amount
    deposit_bonus_package_id UNIQUEIDENTIFIER NULL, -- Link to bonus package if applicable
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    transaction_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (deposit_bonus_package_id) REFERENCES deposit_bonus_package(package_id)
);
CREATE INDEX idx_deposit_student ON deposit (student_id);
CREATE INDEX idx_deposit_transaction_date ON deposit (transaction_date);
CREATE INDEX idx_deposit_payment_status ON deposit (payment_status);
CREATE INDEX idx_deposit_bonus_package ON deposit (deposit_bonus_package_id);
GO

-- Semester bonus table - defines how much money is given per semester
CREATE TABLE semester_bonus (
    bonus_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    semester_id UNIQUEIDENTIFIER NOT NULL,
    bonus_amount DECIMAL(10, 2) NOT NULL CHECK (bonus_amount >= 0), -- Amount of in-app currency given
    description NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id),
    UNIQUE (semester_id)
);
CREATE INDEX idx_semester_bonus_semester ON semester_bonus (semester_id);
GO

-- Student semester bonus table - tracks which students received semester bonuses
CREATE TABLE student_semester_bonus (
    student_bonus_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_bonus_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL, -- Denormalized for easier querying
    received BIT NOT NULL DEFAULT 0, -- Whether student has received the bonus
    received_date DATETIME NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (semester_bonus_id) REFERENCES semester_bonus(bonus_id),
    FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    UNIQUE (student_id, semester_id)
);
CREATE INDEX idx_student_semester_bonus_student ON student_semester_bonus (student_id);
CREATE INDEX idx_student_semester_bonus_semester ON student_semester_bonus (semester_id);
CREATE INDEX idx_student_semester_bonus_received ON student_semester_bonus (received);
GO

-- Constraint: Students cannot receive semester bonus before their enrollment date
-- This is enforced via a trigger or application logic since CHECK constraints cannot reference other tables
-- Application should validate: semester.start_date >= student.enrollment_date before inserting
GO

-- ============================================
-- Pricing Configuration Tables
-- ============================================

-- Color mode table - defines available color modes
CREATE TABLE color_mode (
    color_mode_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    color_mode_name NVARCHAR(50) NOT NULL UNIQUE, -- e.g., 'color', 'grayscale', 'black-white'
    description NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_color_mode_name ON color_mode (color_mode_name);
GO

-- Color mode price table - defines color mode pricing configurations
CREATE TABLE color_mode_price (
    setting_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    color_mode_id UNIQUEIDENTIFIER NOT NULL,
    price_per_page DECIMAL(10, 4) NOT NULL CHECK (price_per_page >= 0), -- Price per page in dollars for this color mode
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (color_mode_id) REFERENCES color_mode(color_mode_id)
);
CREATE INDEX idx_color_mode_price_color_mode ON color_mode_price (color_mode_id);
CREATE INDEX idx_color_mode_price_active ON color_mode_price (is_active);
GO

-- Page size price table - defines base price per page for each paper size
CREATE TABLE page_size_price (
    price_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    page_size_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    page_price DECIMAL(10, 4) NOT NULL CHECK (page_price >= 0), -- Price per page in dollars
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (page_size_id) REFERENCES page_size(page_size_id)
);
CREATE INDEX idx_page_size_price_page_size ON page_size_price (page_size_id);
CREATE INDEX idx_page_size_price_active ON page_size_price (is_active);
GO

-- Page discount package - defines volume discounts based on number of pages
CREATE TABLE page_discount_package (
    package_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    min_pages INT NOT NULL CHECK (min_pages > 0), -- Minimum pages to qualify
    discount_percentage DECIMAL(5, 4) NOT NULL CHECK (discount_percentage >= 0 AND discount_percentage <= 1), -- Discount (0-1 range)
    package_name NVARCHAR(200),
    description NVARCHAR(200),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_page_discount_package_min_pages ON page_discount_package (min_pages);
CREATE INDEX idx_page_discount_package_active ON page_discount_package (is_active);
GO

-- Fund and Supplier Paper Purchase Management Tables
-- ============================================

CREATE TABLE fund_source (
    fund_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    fund_source_type VARCHAR(50) NOT NULL CHECK (fund_source_type IN ('school_budget', 'donation', 'revenue', 'other')),
    fund_source_name NVARCHAR(255),
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    received_date DATE NOT NULL,
    description NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_fund_source_type ON fund_source (fund_source_type);
CREATE INDEX idx_fund_received_date ON fund_source (received_date);
GO

CREATE TABLE supplier_paper_purchase (
    purchase_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    supplier_name NVARCHAR(255) NOT NULL,
    supplier_contact VARCHAR(255),
    purchase_date DATE NOT NULL,
    total_amount_paid DECIMAL(12, 2) NOT NULL CHECK (total_amount_paid >= 0),
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    invoice_number VARCHAR(100),
    notes NVARCHAR(200),
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_purchase_date ON supplier_paper_purchase (purchase_date);
CREATE INDEX idx_payment_status ON supplier_paper_purchase (payment_status);
CREATE INDEX idx_supplier_name ON supplier_paper_purchase (supplier_name);
GO

CREATE TABLE paper_purchase_item (
    purchase_item_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    purchase_id UNIQUEIDENTIFIER NOT NULL,
    page_size_id UNIQUEIDENTIFIER NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 4) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(12, 2) NOT NULL CHECK (total_price >= 0),
    received_quantity INT NULL,
    received_date DATE NULL,
    notes NVARCHAR(200),
    FOREIGN KEY (purchase_id) REFERENCES supplier_paper_purchase(purchase_id) ON DELETE CASCADE,
    FOREIGN KEY (page_size_id) REFERENCES page_size(page_size_id),
    CHECK (received_quantity IS NULL OR received_quantity >= 0)
);
CREATE INDEX idx_purchase_id ON paper_purchase_item (purchase_id);
CREATE INDEX idx_page_size ON paper_purchase_item (page_size_id);
GO

-- System Configuration Tables
-- ============================================

CREATE TABLE system_configuration (
    config_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value NVARCHAR(200) NOT NULL,
    description NVARCHAR(200),
    updated_at DATETIME DEFAULT GETDATE(),
    updated_by UNIQUEIDENTIFIER,
    FOREIGN KEY (updated_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_config_key ON system_configuration (config_key);
GO

CREATE TABLE permitted_file_type (
    file_type_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    file_extension VARCHAR(10) NOT NULL UNIQUE,
    mime_type VARCHAR(100),
    description NVARCHAR(100),
    is_permitted BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    updated_by UNIQUEIDENTIFIER,
    FOREIGN KEY (updated_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_extension ON permitted_file_type (file_extension);
CREATE INDEX idx_permitted ON permitted_file_type (is_permitted);
GO

-- Print Job Management Tables
-- ============================================

-- Uploaded files: documents saved by students before/for printing
CREATE TABLE uploaded_file (
    uploaded_file_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    file_name NVARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size_kb INT,
    file_url VARCHAR(500) NOT NULL,
    page_count INT NULL, -- Số trang của file (tính khi upload: PDFBox cho PDF, ConvertAPI + PDFBox cho DOCX/DOC, POI cho Office files)
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);
CREATE INDEX idx_uploaded_file_student ON uploaded_file (student_id);
CREATE INDEX idx_uploaded_file_created_at ON uploaded_file (created_at);
CREATE INDEX idx_uploaded_file_page_count ON uploaded_file (page_count);
GO

CREATE TABLE print_job (
    job_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    printer_id UNIQUEIDENTIFIER NOT NULL,
    uploaded_file_id UNIQUEIDENTIFIER NOT NULL, -- References uploaded_file record used for this job
    page_size_price_id UNIQUEIDENTIFIER NOT NULL, -- References which page_size_price configuration was used (contains page_size_id)
    color_mode_price_id UNIQUEIDENTIFIER NOT NULL, -- References which color_mode_price configuration was used
    page_discount_package_id UNIQUEIDENTIFIER NULL, -- Which bulk discount was applied (if any)
    page_orientation VARCHAR(20) NOT NULL DEFAULT 'portrait' CHECK (page_orientation IN ('portrait', 'landscape')),
    print_side VARCHAR(20) NOT NULL DEFAULT 'one-sided' CHECK (print_side IN ('one-sided', 'double-sided')),
    number_of_copy INT NOT NULL DEFAULT 1,
    -- Pricing calculation columns (stored for historical accuracy and performance)
    total_pages INT NOT NULL CHECK (total_pages > 0), -- Total number of pages (from print_job_page count)
    subtotal_before_discount DECIMAL(10, 2) NOT NULL CHECK (subtotal_before_discount >= 0), -- Calculated from referenced prices
    discount_percentage DECIMAL(5, 4) NULL CHECK (discount_percentage IS NULL OR (discount_percentage >= 0 AND discount_percentage <= 1)), -- From page_discount_package if applicable
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0), -- Calculated discount amount
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0), -- Final price after discount
    payment_method VARCHAR(50) NULL, -- Payment method selected when creating job: 'balance' or 'qr' (SePay)
    print_status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (print_status IN ('queued', 'printing', 'completed', 'failed', 'cancelled', 'pending_payment')),
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id),
    FOREIGN KEY (uploaded_file_id) REFERENCES uploaded_file(uploaded_file_id),
    FOREIGN KEY (page_size_price_id) REFERENCES page_size_price(price_id),
    FOREIGN KEY (color_mode_price_id) REFERENCES color_mode_price(setting_id),
    FOREIGN KEY (page_discount_package_id) REFERENCES page_discount_package(package_id)
);
CREATE INDEX idx_student_job ON print_job (student_id);
CREATE INDEX idx_printer_job ON print_job (printer_id);
CREATE INDEX idx_print_status ON print_job (print_status);
CREATE INDEX idx_created_at ON print_job (created_at);
CREATE INDEX idx_start_time ON print_job (start_time);
CREATE INDEX idx_end_time ON print_job (end_time);
CREATE INDEX idx_page_size_price ON print_job (page_size_price_id);
CREATE INDEX idx_color_mode_price ON print_job (color_mode_price_id);
CREATE INDEX idx_page_discount_package ON print_job (page_discount_package_id);
-- Composite index for queue queries (optimize finding queued/printing jobs by printer)
CREATE INDEX idx_print_job_printer_status_created ON print_job(printer_id, print_status, created_at);
-- Index for progress queries (optimize finding printing jobs)
CREATE INDEX idx_print_job_status_start_time ON print_job(print_status, start_time);
GO

-- Refund table for cancelled print jobs (refund remaining pages)
CREATE TABLE refund_print_job (
    refund_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    pages_not_printed INT NOT NULL CHECK (pages_not_printed >= 0),
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (job_id) REFERENCES print_job(job_id) ON DELETE CASCADE
);
CREATE INDEX idx_refund_job ON refund_print_job (job_id);
GO

CREATE TABLE print_job_page (
    page_record_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id UNIQUEIDENTIFIER NOT NULL,
    page_number INT NOT NULL,
    is_printed BIT DEFAULT 0 NOT NULL,  -- Track if page has been printed (for progress calculation)
    printed_at DATETIME2 NULL,          -- Timestamp when page was printed
    FOREIGN KEY (job_id) REFERENCES print_job(job_id) ON DELETE CASCADE,
    UNIQUE (job_id, page_number)
);
CREATE INDEX idx_job_id ON print_job_page (job_id);
CREATE INDEX idx_print_job_page_job_printed ON print_job_page(job_id, is_printed);  -- Index for counting printed pages
GO

-- Payment table - tracks payments for print jobs
CREATE TABLE payment (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id UNIQUEIDENTIFIER NOT NULL UNIQUE, -- One payment per print job
    student_id UNIQUEIDENTIFIER NOT NULL,
    amount_paid_directly DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (amount_paid_directly >= 0), -- Paid with real money/card
    amount_paid_from_balance DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (amount_paid_from_balance >= 0), -- Paid from in-app balance
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount > 0), -- Total payment amount
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_code VARCHAR(20) NULL, -- Payment code for QR code (format: SIUJOB + 8 chars)
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded', 'expired')),
    expired_at DATETIME NULL, -- Expiration time for QR payment
    transaction_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (job_id) REFERENCES print_job(job_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE NO ACTION,
    CHECK (amount_paid_directly + amount_paid_from_balance = total_amount)
);
CREATE INDEX idx_payment_job ON payment (job_id);
CREATE INDEX idx_payment_student ON payment (student_id);
CREATE INDEX idx_payment_transaction_date ON payment (transaction_date);
CREATE INDEX idx_payment_status ON payment (payment_status);
CREATE INDEX idx_payment_code ON payment (payment_code);
CREATE INDEX idx_payment_expired_at ON payment (expired_at);
GO

-- Student Wallet Ledger Table - Central ledger for all financial transactions
-- ============================================
-- This table implements a ledger pattern: every financial transaction (deposit, payment, refund, bonus)
-- creates one or more ledger entries. This provides a complete audit trail and enables
-- efficient balance calculation and transaction history queries.
CREATE TABLE student_wallet_ledger (
    ledger_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL, -- Amount (positive for IN, negative for OUT)
    direction VARCHAR(3) NOT NULL CHECK (direction IN ('IN', 'OUT')), -- Transaction direction
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('DEPOSIT', 'SEMESTER_BONUS', 'PAYMENT', 'REFUND')), -- Type of transaction
    source_table VARCHAR(50) NOT NULL, -- Source table name (e.g., 'deposit', 'payment', 'refund_print_job', 'student_semester_bonus')
    source_id UNIQUEIDENTIFIER NOT NULL, -- ID of the record in source_table
    description NVARCHAR(255), -- Human-readable description
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);
CREATE INDEX idx_ledger_student ON student_wallet_ledger (student_id);
CREATE INDEX idx_ledger_student_created ON student_wallet_ledger (student_id, created_at);
CREATE INDEX idx_ledger_source ON student_wallet_ledger (source_table, source_id);
CREATE INDEX idx_ledger_source_type ON student_wallet_ledger (source_type);
CREATE INDEX idx_ledger_direction ON student_wallet_ledger (direction);
CREATE INDEX idx_ledger_created_at ON student_wallet_ledger (created_at);
GO

-- Notification table - per-student notifications (topup success, print job status, etc.)
CREATE TABLE notification (
    notification_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- e.g. 'DEPOSIT_COMPLETED', 'PRINT_JOB_COMPLETED', 'PRINT_JOB_FAILED'
    title NVARCHAR(200) NOT NULL,
    message NVARCHAR(1000) NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE
);
CREATE INDEX idx_notification_student ON notification (student_id, created_at);
CREATE INDEX idx_notification_unread ON notification (student_id, is_read, created_at);
GO

-- Audit and Logging Tables
-- ============================================

CREATE TABLE printer_log (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    printer_id UNIQUEIDENTIFIER NOT NULL,
    log_type VARCHAR(30) NOT NULL CHECK (log_type IN 
        ('print_job', 'error', 'maintenance', 'status_change', 'configuration', 'admin_action')),
    severity VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (severity IN 
        ('info', 'warning', 'error', 'critical')),
    description NVARCHAR(500) NOT NULL,
    
    -- Optional reference to related entities
    job_id UNIQUEIDENTIFIER NULL, -- Link to print_job if log_type = 'print_job'
    user_id UNIQUEIDENTIFIER NULL, -- User who triggered the action (student or staff)
    
    -- Additional details stored as JSON for flexibility
    details NVARCHAR(MAX) NULL, -- JSON field for additional context
    
    -- Error/issue tracking
    error_code VARCHAR(50) NULL,
    is_resolved BIT DEFAULT 0,
    resolved_at DATETIME NULL,
    resolved_by UNIQUEIDENTIFIER NULL,
    resolution_notes NVARCHAR(500) NULL,
    
    -- Metadata
    ip_address VARCHAR(45) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    
    -- Foreign Keys
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES print_job(job_id),
    FOREIGN KEY (user_id) REFERENCES [user](user_id),
    FOREIGN KEY (resolved_by) REFERENCES [user](user_id)
);
-- Indexes for efficient querying
CREATE INDEX idx_printer_log_printer ON printer_log(printer_id);
CREATE INDEX idx_printer_log_type ON printer_log(log_type);
CREATE INDEX idx_printer_log_severity ON printer_log(severity);
CREATE INDEX idx_printer_log_created ON printer_log(created_at);
CREATE INDEX idx_printer_log_job ON printer_log(job_id);
CREATE INDEX idx_printer_log_user ON printer_log(user_id);
CREATE INDEX idx_printer_log_resolved ON printer_log(is_resolved);
CREATE INDEX idx_printer_log_type_severity ON printer_log(log_type, severity);
CREATE INDEX idx_printer_log_printer_date ON printer_log(printer_id, created_at);
GO

CREATE TABLE system_audit_log (
    audit_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name NVARCHAR(100) NOT NULL,
    record_id UNIQUEIDENTIFIER NULL,
    previous_audit_id UNIQUEIDENTIFIER NULL,
    changed_field NVARCHAR(MAX) NULL,
    ip_address VARCHAR(45),
    user_agent NVARCHAR(MAX) NULL,
    action_timestamp DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_system_audit_log_user FOREIGN KEY (user_id) REFERENCES [user](user_id),
    CONSTRAINT FK_system_audit_log_previous FOREIGN KEY (previous_audit_id) REFERENCES system_audit_log(audit_id)
);
CREATE INDEX idx_user_audit ON system_audit_log(user_id);
CREATE INDEX idx_action_timestamp ON system_audit_log(action_timestamp);
CREATE INDEX idx_table_name ON system_audit_log(table_name);
CREATE INDEX idx_record_id ON system_audit_log(record_id);
CREATE INDEX idx_previous_audit ON system_audit_log(previous_audit_id);
GO
-- ============================================
-- Composite Indexes for Query Optimization
-- ============================================

CREATE INDEX idx_print_job_student_date ON print_job(student_id, created_at);
CREATE INDEX idx_print_job_printer_date ON print_job(printer_id, created_at);
CREATE INDEX idx_print_job_status_date ON print_job(print_status, created_at);
GO

-- ============================================
-- Views for Common Queries and Reports
-- ============================================

-- View: Student balance (computed from student_wallet_ledger - single source of truth)
CREATE VIEW student_balance_view AS
SELECT 
    s.student_id,
    s.student_code,
    u.full_name,
    u.email,
    -- Calculate balance from student_wallet_ledger (single source of truth)
    -- This ensures all ledger entries (including manual adjustments) are included
    COALESCE((
        SELECT SUM(swl.amount)
        FROM student_wallet_ledger swl
        WHERE swl.student_id = s.student_id
    ), 0) AS balance_amount
FROM student s
JOIN [user] u ON s.user_id = u.user_id;
GO

-- View: Student print summary
CREATE VIEW student_print_summary AS
WITH job_pages AS (
    SELECT job_id, COUNT(*) AS page_count
    FROM print_job_page
    GROUP BY job_id
)
SELECT 
    s.student_id,
    s.student_code,
    u.full_name,
    u.email,
    c.class_name,
    m.major_name,
    d.department_name,
    f.faculty_name,
    ay.year_name,
    COUNT(DISTINCT pj.job_id) AS total_print_job,
    COALESCE(SUM(jp.page_count * pj.number_of_copy), 0) AS total_pages_printed,
    COALESCE(SUM(p.total_amount), 0) AS total_amount_spent
FROM student s
JOIN [user] u ON s.user_id = u.user_id
JOIN class c ON s.class_id = c.class_id
JOIN major m ON c.major_id = m.major_id
JOIN department d ON m.department_id = d.department_id
JOIN faculty f ON d.faculty_id = f.faculty_id
JOIN academic_year ay ON c.academic_year_id = ay.academic_year_id
LEFT JOIN print_job pj ON s.student_id = pj.student_id AND pj.print_status = 'completed'
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
LEFT JOIN payment p ON pj.job_id = p.job_id AND p.payment_status = 'completed'
GROUP BY s.student_id, s.student_code, u.full_name, u.email, 
         c.class_name, m.major_name, d.department_name, f.faculty_name, ay.year_name;
GO
-- View: Printer usage statistics
CREATE VIEW printer_usage_statistic AS
WITH job_pages AS (
    SELECT job_id, COUNT(*) AS page_count
    FROM print_job_page
    GROUP BY job_id
)
SELECT 
    pp.printer_id,
    b.brand_name,
    pm.model_name,
    bld.campus_name,
    bld.address AS building_address,
    r.room_code,
    r.room_type,
    pp.is_enabled,
    COUNT(DISTINCT pj.job_id) AS total_job,
    COUNT(DISTINCT pj.student_id) AS unique_student_count,
    COALESCE(SUM(jp.page_count * pj.number_of_copy), 0) AS total_page_printed,
    MAX(pj.end_time) AS last_print_time
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN floor f ON r.floor_id = f.floor_id
JOIN building bld ON f.building_id = bld.building_id
LEFT JOIN print_job pj ON pp.printer_id = pj.printer_id AND pj.print_status = 'completed'
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
GROUP BY pp.printer_id, b.brand_name, pm.model_name, bld.campus_name, bld.address, r.room_code, r.room_type, pp.is_enabled;
GO
-- View: Monthly reports (automated)
CREATE VIEW monthly_report AS
WITH job_pages AS (
    SELECT job_id, COUNT(*) AS page_count
    FROM print_job_page
    GROUP BY job_id
)
SELECT 
    YEAR(pj.end_time) AS report_year,
    MONTH(pj.end_time) AS report_month,
    COUNT(DISTINCT pj.job_id) AS total_print_job,
    COUNT(DISTINCT pj.student_id) AS total_student_used,
    COUNT(DISTINCT pj.printer_id) AS total_printer_used,
    COALESCE(SUM(jp.page_count * pj.number_of_copy), 0) AS total_pages_printed,
    COALESCE(SUM(p.total_amount), 0) AS total_revenue
FROM print_job pj
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
LEFT JOIN payment p ON pj.job_id = p.job_id AND p.payment_status = 'completed'
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY YEAR(pj.end_time), MONTH(pj.end_time);
GO
-- View: Yearly reports (automated)
CREATE VIEW yearly_report AS
WITH job_pages AS (
    SELECT job_id, COUNT(*) AS page_count
    FROM print_job_page
    GROUP BY job_id
)
SELECT 
    YEAR(pj.end_time) AS report_year,
    COUNT(DISTINCT pj.job_id) AS total_print_job,
    COUNT(DISTINCT pj.student_id) AS total_student_used,
    COUNT(DISTINCT pj.printer_id) AS total_printer_used,
    COALESCE(SUM(jp.page_count * pj.number_of_copy), 0) AS total_pages_printed,
    COALESCE(SUM(p.total_amount), 0) AS total_revenue
FROM print_job pj
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
LEFT JOIN payment p ON pj.job_id = p.job_id AND p.payment_status = 'completed'
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY YEAR(pj.end_time);
GO
-- View: Student printing history with details
CREATE VIEW student_printing_history AS
SELECT 
    pj.job_id,
    s.student_id,
    s.student_code,
    u.full_name AS student_name,
    c.class_name,
    m.major_name,
    d.department_name,
    f.faculty_name,
    uf.file_name,
    uf.file_type,
    uf.file_url,
    ps.size_name AS paper_size,
    pj.print_side,
    cm.color_mode_name AS color_mode,
    pj.number_of_copy,
    COUNT(pjp.page_number) AS page_count,
    COUNT(pjp.page_number) * pj.number_of_copy AS total_pages,
    b.brand_name AS printer_brand,
    pm.model_name AS printer_model,
    bld.campus_name,
    bld.address AS building_address,
    r.room_code,
    r.room_type,
    pj.print_status,
    pj.start_time,
    pj.end_time
FROM print_job pj
JOIN student s ON pj.student_id = s.student_id
JOIN [user] u ON s.user_id = u.user_id
JOIN class c ON s.class_id = c.class_id
JOIN major m ON c.major_id = m.major_id
JOIN department d ON m.department_id = d.department_id
JOIN faculty f ON d.faculty_id = f.faculty_id
JOIN printer_physical pp ON pj.printer_id = pp.printer_id
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN floor fl ON r.floor_id = fl.floor_id
JOIN building bld ON fl.building_id = bld.building_id
JOIN uploaded_file uf ON pj.uploaded_file_id = uf.uploaded_file_id
JOIN page_size_price psp ON pj.page_size_price_id = psp.price_id
JOIN page_size ps ON psp.page_size_id = ps.page_size_id
JOIN color_mode_price cmp ON pj.color_mode_price_id = cmp.setting_id
JOIN color_mode cm ON cmp.color_mode_id = cm.color_mode_id
LEFT JOIN print_job_page pjp ON pj.job_id = pjp.job_id
GROUP BY pj.job_id, s.student_id, s.student_code, u.full_name, 
         c.class_name, m.major_name, d.department_name, f.faculty_name, fl.floor_id,
         uf.file_name, uf.file_type, uf.file_url,
         ps.size_name, pj.print_side, cm.color_mode_name, pj.number_of_copy,
         b.brand_name, pm.model_name, bld.campus_name, bld.address, 
         r.room_code, r.room_type, pj.print_status, pj.start_time, pj.end_time;
GO

-- View: Print job pricing details (reads stored pricing fields)
CREATE VIEW print_job_pricing AS
SELECT 
    pj.job_id,
    pj.student_id,
    pj.printer_id,
    psp.page_size_id AS paper_size_id,
    pj.page_size_price_id,
    pj.color_mode_price_id,
    pj.page_discount_package_id,
    pj.number_of_copy,
    -- Use stored total_pages from print_job table
    pj.total_pages,
    -- Get prices from referenced configurations
    psp.page_price AS base_price_per_page,
    cmp.price_per_page AS color_mode_price_per_page,
    -- Use stored pricing values from print_job table
    pj.subtotal_before_discount,
    pj.discount_percentage,
    pj.discount_amount,
    pj.total_price
FROM print_job pj
JOIN page_size_price psp ON pj.page_size_price_id = psp.price_id
JOIN color_mode_price cmp ON pj.color_mode_price_id = cmp.setting_id
JOIN color_mode cm ON cmp.color_mode_id = cm.color_mode_id
LEFT JOIN page_discount_package pdp ON pj.page_discount_package_id = pdp.package_id;
GO

-- View: Active printers with full details
CREATE VIEW active_printer_detail AS
SELECT 
    pp.printer_id,
    b.brand_name,
    pm.model_name,
    pm.description AS model_description,
    ps.size_name AS max_paper_size,
    pm.supports_color,
    pm.supports_duplex,
    pp.serial_number,
    bld.campus_name,
    bld.building_code,
    bld.address AS building_address,
    r.room_code,
    r.room_type,
    pp.installed_date,
    pp.last_maintenance_date,
    pp.is_enabled,
    CONCAT(bld.campus_name, ' - ', bld.building_code, ' - Room ', r.room_code) AS full_location
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN floor f ON r.floor_id = f.floor_id
JOIN building bld ON f.building_id = bld.building_id
JOIN page_size ps ON pm.max_paper_size_id = ps.page_size_id
WHERE pp.is_enabled = 1;
GO


-- View: Daily printing activity
CREATE VIEW daily_printing_activity AS
WITH job_pages AS (
    SELECT job_id, COUNT(*) AS page_count
    FROM print_job_page
    GROUP BY job_id
)
SELECT 
    CAST(pj.end_time AS DATE) AS print_date,
    COUNT(DISTINCT pj.job_id) AS total_job,
    COUNT(DISTINCT pj.student_id) AS unique_student,
    COUNT(DISTINCT pj.printer_id) AS printer_used,
    COALESCE(SUM(jp.page_count * pj.number_of_copy), 0) AS total_pages_printed,
    COALESCE(SUM(p.total_amount), 0) AS total_revenue
FROM print_job pj
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
LEFT JOIN payment p ON pj.job_id = p.job_id AND p.payment_status = 'completed'
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY CAST(pj.end_time AS DATE);
GO

-- View: Printer maintenance schedule
CREATE VIEW printer_maintenance_status AS
SELECT 
    pp.printer_id,
    b.brand_name,
    pm.model_name,
    bld.campus_name,
    bld.building_code,
    bld.address AS building_address,
    r.room_code,
    r.room_type,
    pp.installed_date,
    pp.last_maintenance_date,
    DATEDIFF(DAY, pp.last_maintenance_date, GETDATE()) AS days_since_maintenance,
    COUNT(pj.job_id) AS job_count_since_maintenance
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN floor f ON r.floor_id = f.floor_id
JOIN building bld ON f.building_id = bld.building_id
LEFT JOIN print_job pj ON pp.printer_id = pj.printer_id 
    AND pj.end_time > pp.last_maintenance_date
WHERE pp.is_enabled = 1
GROUP BY pp.printer_id, b.brand_name, pm.model_name, bld.campus_name, 
         bld.building_code, bld.address, r.room_code, r.room_type, pp.installed_date, pp.last_maintenance_date;
GO

-- ============================================
-- View for Dashboard Log Display
-- ============================================

CREATE VIEW printer_log_dashboard AS
SELECT 
    pl.log_id,
    pl.created_at AS timestamp,
    pp.printer_id,
    CONCAT(bld.building_code, '-', r.room_code) AS printer_location,
    b.brand_name + ' ' + pm.model_name AS printer_name,
    pl.log_type AS type,
    pl.severity,
    pl.description,
    pl.error_code,
    pl.is_resolved,
    u.full_name AS user_name,
    u.user_type,
    uf.file_url AS related_file,
    pl.details
FROM printer_log pl
JOIN printer_physical pp ON pl.printer_id = pp.printer_id
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN floor f ON r.floor_id = f.floor_id
JOIN building bld ON f.building_id = bld.building_id
LEFT JOIN [user] u ON pl.user_id = u.user_id
LEFT JOIN print_job pj ON pl.job_id = pj.job_id
LEFT JOIN uploaded_file uf ON pj.uploaded_file_id = uf.uploaded_file_id;
GO

-- ============================================
-- View for Log Statistics (for dashboard summary)
-- ============================================

CREATE VIEW printer_log_statistics AS
SELECT 
    COUNT(*) AS total_entries,
    SUM(CASE WHEN severity = 'error' THEN 1 ELSE 0 END) AS error_count,
    SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN severity = 'info' THEN 1 ELSE 0 END) AS info_count,
    SUM(CASE WHEN severity IN ('error', 'critical') AND is_resolved = 0 THEN 1 ELSE 0 END) AS unresolved_critical_count
FROM printer_log
WHERE created_at >= DATEADD(DAY, -30, GETDATE()); -- Last 30 days
GO

CREATE TABLE refresh_token (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    token NVARCHAR(500) NOT NULL UNIQUE,
    user_id UNIQUEIDENTIFIER NOT NULL,
    expiry_date DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    revoked BIT NULL DEFAULT 0,
    CONSTRAINT FK_refresh_token_user FOREIGN KEY (user_id) REFERENCES [user](user_id)
);

CREATE INDEX idx_token ON refresh_token(token);
CREATE INDEX idx_user_id ON refresh_token(user_id);
CREATE INDEX idx_expiry_date ON refresh_token(expiry_date);


CREATE TABLE password_reset_token (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    token NVARCHAR(500) NOT NULL UNIQUE,
    user_id UNIQUEIDENTIFIER NOT NULL,
    expiry_date DATETIME NOT NULL,
    used BIT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_password_reset_token_user FOREIGN KEY (user_id) REFERENCES [user](user_id)
);

-- Indexes
CREATE INDEX idx_reset_token ON password_reset_token(token);
CREATE INDEX idx_reset_user_id ON password_reset_token(user_id);
CREATE INDEX idx_reset_expiry_date ON password_reset_token(expiry_date);