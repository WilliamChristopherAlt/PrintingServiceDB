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
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type VARCHAR(10) NOT NULL CHECK (user_type IN ('student', 'staff')),
    phone_number VARCHAR(15),
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
    faculty_name VARCHAR(100) NOT NULL UNIQUE,
    faculty_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    established_date DATE,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_faculty_code ON faculty (faculty_code);
GO

CREATE TABLE department (
    department_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_id UNIQUEIDENTIFIER NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
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
    major_name VARCHAR(100) NOT NULL,
    major_code VARCHAR(20) NOT NULL UNIQUE,
    degree_type VARCHAR(20) NOT NULL DEFAULT 'bachelor' CHECK (degree_type IN ('bachelor', 'master', 'doctorate')),
    duration_years INT NOT NULL DEFAULT 4,
    description TEXT,
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
    year_name VARCHAR(20) NOT NULL UNIQUE,
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
    class_name VARCHAR(50) NOT NULL,
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
    size_name VARCHAR(20) NOT NULL UNIQUE,
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
    campus_name VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_building_code ON building (building_code);
CREATE INDEX idx_campus_name ON building (campus_name);
GO

CREATE TABLE room (
    room_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_id UNIQUEIDENTIFIER NOT NULL,
    room_code VARCHAR(20) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (building_id) REFERENCES building(building_id),
    UNIQUE (building_id, room_code)
);
CREATE INDEX idx_building_room ON room (building_id);
CREATE INDEX idx_room_code ON room (room_code);
CREATE INDEX idx_room_type ON room (room_type);
GO

-- Printer Management Tables
-- ============================================

CREATE TABLE brand (
    brand_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    brand_name VARCHAR(50) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50),
    website VARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE printer_model (
    model_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    brand_id UNIQUEIDENTIFIER NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    description TEXT,
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
    term_name VARCHAR(10) NOT NULL CHECK (term_name IN ('fall', 'spring', 'summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    UNIQUE (academic_year_id, term_name),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);
CREATE INDEX idx_semester_academic_year ON semester (academic_year_id, term_name);
CREATE INDEX idx_semester_dates ON semester (start_date, end_date);
GO

-- Per-student semester allocation of free pages (A4-equivalent)
CREATE TABLE student_page_allocation (
    allocation_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    a4_page_count INT NOT NULL,
    allocation_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    UNIQUE (student_id, semester_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_student_page_allocation_student ON student_page_allocation (student_id);
CREATE INDEX idx_student_page_allocation_semester ON student_page_allocation (semester_id);
GO

CREATE TABLE discount_pack (
    discount_pack_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    num_pages INT NOT NULL,
    percent_off DECIMAL(5, 4) NOT NULL CHECK (percent_off >= 0 AND percent_off <= 1),
    pack_name VARCHAR(100),
    description TEXT,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
CREATE INDEX idx_num_pages ON discount_pack (num_pages);
CREATE INDEX idx_is_active ON discount_pack (is_active);
GO

CREATE TABLE student_page_purchase (
    purchase_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    page_size_id UNIQUEIDENTIFIER NOT NULL,
    quantity INT NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    discount_pack_id UNIQUEIDENTIFIER NULL, -- Link to discount pack if package was used
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    transaction_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (page_size_id) REFERENCES page_size(page_size_id),
    FOREIGN KEY (discount_pack_id) REFERENCES discount_pack(discount_pack_id)
);
CREATE INDEX idx_student_purchase ON student_page_purchase (student_id);
CREATE INDEX idx_transaction_date ON student_page_purchase (transaction_date);
CREATE INDEX idx_payment_status ON student_page_purchase (payment_status);
CREATE INDEX idx_page_size ON student_page_purchase (page_size_id);
CREATE INDEX idx_discount_pack ON student_page_purchase (discount_pack_id);
GO

-- Fund and Supplier Paper Purchase Management Tables
-- ============================================

CREATE TABLE fund_source (
    fund_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    fund_source_type VARCHAR(50) NOT NULL CHECK (fund_source_type IN ('school_budget', 'donation', 'revenue', 'other')),
    fund_source_name VARCHAR(255),
    amount DECIMAL(12, 2) NOT NULL CHECK (amount > 0),
    received_date DATE NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_fund_source_type ON fund_source (fund_source_type);
CREATE INDEX idx_fund_received_date ON fund_source (received_date);
GO

CREATE TABLE supplier_paper_purchase (
    purchase_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    supplier_name VARCHAR(255) NOT NULL,
    supplier_contact VARCHAR(255),
    purchase_date DATE NOT NULL,
    total_amount_paid DECIMAL(12, 2) NOT NULL CHECK (total_amount_paid >= 0),
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    invoice_number VARCHAR(100),
    notes TEXT,
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
    notes TEXT,
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
    config_value TEXT NOT NULL,
    description TEXT,
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
    description VARCHAR(100),
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

CREATE TABLE print_job (
    job_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    printer_id UNIQUEIDENTIFIER NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size_kb INT,
    paper_size_id UNIQUEIDENTIFIER NOT NULL,
    page_orientation VARCHAR(20) NOT NULL DEFAULT 'portrait' CHECK (page_orientation IN ('portrait', 'landscape')),
    print_side VARCHAR(20) NOT NULL DEFAULT 'one-sided' CHECK (print_side IN ('one-sided', 'double-sided')),
    color_mode VARCHAR(20) NOT NULL DEFAULT 'black-white' CHECK (color_mode IN ('color', 'grayscale', 'black-white')),
    number_of_copy INT NOT NULL DEFAULT 1,
    print_status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (print_status IN ('queued', 'printing', 'completed', 'failed', 'cancelled')),
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id),
    FOREIGN KEY (paper_size_id) REFERENCES page_size(page_size_id)
);
CREATE INDEX idx_student_job ON print_job (student_id);
CREATE INDEX idx_printer_job ON print_job (printer_id);
CREATE INDEX idx_print_status ON print_job (print_status);
CREATE INDEX idx_created_at ON print_job (created_at);
CREATE INDEX idx_start_time ON print_job (start_time);
CREATE INDEX idx_end_time ON print_job (end_time);
CREATE INDEX idx_paper_size ON print_job (paper_size_id);
GO

CREATE TABLE print_job_page (
    page_record_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    job_id UNIQUEIDENTIFIER NOT NULL,
    page_number INT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES print_job(job_id) ON DELETE CASCADE,
    UNIQUE (job_id, page_number)
);
CREATE INDEX idx_job_id ON print_job_page (job_id);
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

-- Printer Activity Log Table (for tracking printer CRUD operations)
-- ============================================
CREATE TABLE printer_activity_log (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    printer_id UNIQUEIDENTIFIER NOT NULL,
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('added', 'enabled', 'disabled', 'updated', 'removed')),
    performed_by UNIQUEIDENTIFIER NULL,
    action_detail TEXT NULL,
    action_timestamp DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_printer_log ON printer_activity_log (printer_id);
CREATE INDEX idx_action_timestamp ON printer_activity_log (action_timestamp);
GO

CREATE TABLE system_audit_log (
    audit_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
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

-- View: Student print summary with balance
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
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count * 2
            WHEN ps.size_name = 'A5' THEN jp.page_count * 0.5
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_printed,
    COALESCE((
        SELECT SUM(
            CASE 
                WHEN psize.size_name = 'A4' THEN spp.quantity
                WHEN psize.size_name = 'A3' THEN spp.quantity * 2
                WHEN psize.size_name = 'A5' THEN spp.quantity * 0.5
                ELSE spp.quantity
            END
        )
        FROM student_page_purchase spp
        JOIN page_size psize ON spp.page_size_id = psize.page_size_id
        WHERE spp.student_id = s.student_id AND spp.payment_status = 'completed'
    ), 0) AS total_a4_page_balance,
    COALESCE((
        SELECT SUM(
            CASE 
                WHEN psize.size_name = 'A4' THEN spp.quantity
                WHEN psize.size_name = 'A3' THEN spp.quantity * 2
                WHEN psize.size_name = 'A5' THEN spp.quantity * 0.5
                ELSE spp.quantity
            END
        )
        FROM student_page_purchase spp
        JOIN page_size psize ON spp.page_size_id = psize.page_size_id
        WHERE spp.student_id = s.student_id AND spp.payment_status = 'completed'
    ), 0) - COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count * 2
            WHEN ps.size_name = 'A5' THEN jp.page_count * 0.5
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS remaining_a4_page
FROM student s
JOIN [user] u ON s.user_id = u.user_id
JOIN class c ON s.class_id = c.class_id
JOIN major m ON c.major_id = m.major_id
JOIN department d ON m.department_id = d.department_id
JOIN faculty f ON d.faculty_id = f.faculty_id
JOIN academic_year ay ON c.academic_year_id = ay.academic_year_id
LEFT JOIN print_job pj ON s.student_id = pj.student_id AND pj.print_status = 'completed'
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
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
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count
            WHEN ps.size_name = 'A5' THEN jp.page_count
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS total_page_printed,
    MAX(pj.end_time) AS last_print_time
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN building bld ON r.building_id = bld.building_id
LEFT JOIN print_job pj ON pp.printer_id = pj.printer_id AND pj.print_status = 'completed'
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
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
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count * 2
            WHEN ps.size_name = 'A5' THEN jp.page_count * 0.5
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
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
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count * 2
            WHEN ps.size_name = 'A5' THEN jp.page_count * 0.5
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page,
    COALESCE(SUM(spp.amount_paid), 0) AS total_revenue
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
LEFT JOIN student s ON pj.student_id = s.student_id
LEFT JOIN student_page_purchase spp ON s.student_id = spp.student_id 
    AND spp.payment_status = 'completed'
    AND YEAR(spp.transaction_date) = YEAR(pj.end_time)
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
    pj.file_name,
    ps.size_name AS paper_size,
    pj.print_side,
    pj.color_mode,
    pj.number_of_copy,
    COUNT(pjp.page_number) AS page_count,
    CASE 
        WHEN ps.size_name = 'A4' THEN COUNT(pjp.page_number)
        WHEN ps.size_name = 'A3' THEN COUNT(pjp.page_number) * 2
        WHEN ps.size_name = 'A5' THEN COUNT(pjp.page_number) * 0.5
        ELSE COUNT(pjp.page_number)
    END * pj.number_of_copy AS a4_equivalent,
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
JOIN building bld ON r.building_id = bld.building_id
JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN print_job_page pjp ON pj.job_id = pjp.job_id
GROUP BY pj.job_id, s.student_id, s.student_code, u.full_name, 
         c.class_name, m.major_name, d.department_name, f.faculty_name,
         pj.file_name, ps.size_name, pj.print_side, pj.color_mode, pj.number_of_copy,
         b.brand_name, pm.model_name, bld.campus_name, bld.address, 
         r.room_code, r.room_type, pj.print_status, pj.start_time, pj.end_time;
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
JOIN building bld ON r.building_id = bld.building_id
JOIN page_size ps ON pm.max_paper_size_id = ps.page_size_id
WHERE pp.is_enabled = 1;
GO

-- View: Page purchase summary by student
CREATE VIEW student_page_purchase_summary AS
SELECT 
    s.student_id,
    s.student_code,
    u.full_name,
    COUNT(spp.purchase_id) AS total_transaction,
    SUM(CASE 
        WHEN spp.payment_status = 'completed' THEN 
            CASE 
                WHEN ps.size_name = 'A4' THEN spp.quantity
                WHEN ps.size_name = 'A3' THEN spp.quantity * 2
                WHEN ps.size_name = 'A5' THEN spp.quantity * 0.5
                ELSE spp.quantity
            END
        ELSE 0 
    END) AS total_a4_equivalent_purchased,
    SUM(CASE WHEN spp.payment_status = 'completed' THEN spp.amount_paid ELSE 0 END) AS total_amount_paid,
    MAX(spp.transaction_date) AS last_purchase_date
FROM student s
JOIN [user] u ON s.user_id = u.user_id
LEFT JOIN student_page_purchase spp ON s.student_id = spp.student_id
LEFT JOIN page_size ps ON spp.page_size_id = ps.page_size_id
GROUP BY s.student_id, s.student_code, u.full_name;
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
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN jp.page_count
            WHEN ps.size_name = 'A3' THEN jp.page_count * 2
            WHEN ps.size_name = 'A5' THEN jp.page_count * 0.5
            ELSE jp.page_count
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN job_pages jp ON pj.job_id = jp.job_id
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
JOIN building bld ON r.building_id = bld.building_id
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
    pj.file_name AS related_file,
    pl.details
FROM printer_log pl
JOIN printer_physical pp ON pl.printer_id = pp.printer_id
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN room r ON pp.room_id = r.room_id
JOIN building bld ON r.building_id = bld.building_id
LEFT JOIN [user] u ON pl.user_id = u.user_id
LEFT JOIN print_job pj ON pl.job_id = pj.job_id;
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