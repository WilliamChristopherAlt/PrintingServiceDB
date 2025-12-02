-- ============================================
-- HCMSIU Student Smart Printing Service (SSPS)
-- Database Schema
-- ============================================
-- SPSO = Student Printing Service Officer (staff managing the system)
-- ============================================

-- CREATE DATABASE IF NOT EXISTS printing_service_db;

USE printing_service_db
GO;

-- User Management Tables
-- ============================================

CREATE TABLE user (
    user_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(255) NOT NULL,
    user_type ENUM('student', 'staff') NOT NULL,
    phone_number VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_user_type (user_type),
    INDEX idx_email (email)
);

-- Academic Structure Tables
-- ============================================

CREATE TABLE faculty (
    faculty_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    faculty_name VARCHAR(100) NOT NULL UNIQUE,
    faculty_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    established_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_faculty_code (faculty_code)
);

CREATE TABLE department (
    department_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    faculty_id CHAR(36) NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    department_code VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    established_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    INDEX idx_faculty (faculty_id),
    INDEX idx_department_code (department_code),
    UNIQUE KEY unique_faculty_department (faculty_id, department_name)
);

CREATE TABLE major (
    major_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    department_id CHAR(36) NOT NULL,
    major_name VARCHAR(100) NOT NULL,
    major_code VARCHAR(20) NOT NULL UNIQUE,
    degree_type ENUM('bachelor', 'master', 'doctorate') NOT NULL DEFAULT 'bachelor',
    duration_years INT NOT NULL DEFAULT 4,
    description TEXT,
    established_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES department(department_id),
    INDEX idx_department (department_id),
    INDEX idx_major_code (major_code),
    UNIQUE KEY unique_department_major (department_id, major_name)
);

CREATE TABLE academic_year (
    academic_year_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    year_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_year_name (year_name),
    INDEX idx_date_range (start_date, end_date)
);

CREATE TABLE class (
    class_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    major_id CHAR(36) NOT NULL,
    academic_year_id CHAR(36) NOT NULL,
    class_name VARCHAR(50) NOT NULL,
    class_code VARCHAR(20) NOT NULL UNIQUE,
    year_level INT NOT NULL, -- 1, 2, 3, 4 for bachelor; 1, 2 for master, etc.
    max_students INT DEFAULT 40,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (major_id) REFERENCES major(major_id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id),
    INDEX idx_major (major_id),
    INDEX idx_academic_year (academic_year_id),
    INDEX idx_class_code (class_code),
    UNIQUE KEY unique_major_year_class (major_id, academic_year_id, class_name)
);

CREATE TABLE student (
    student_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL UNIQUE,
    student_code VARCHAR(20) NOT NULL UNIQUE,
    class_id CHAR(36) NOT NULL,
    enrollment_date DATE,
    graduation_date DATE NULL,
    status ENUM('active', 'graduated', 'suspended', 'withdrawn') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES class(class_id),
    INDEX idx_student_code (student_code),
    INDEX idx_class (class_id),
    INDEX idx_status (status)
);

CREATE TABLE staff (
    staff_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL UNIQUE,
    employee_code VARCHAR(20) NOT NULL UNIQUE,
    position ENUM('manager', 'technician', 'administrator', 'supervisor') NOT NULL,
    hire_date DATE,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    INDEX idx_employee_code (employee_code)
);

-- Printer Management Tables
-- ============================================

CREATE TABLE brand (
    brand_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    brand_name VARCHAR(50) NOT NULL UNIQUE,
    country_of_origin VARCHAR(50),
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE printer_model (
    model_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    brand_id CHAR(36) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    description TEXT,
    max_paper_size_id CHAR(36) NOT NULL,
    supports_color BOOLEAN DEFAULT FALSE,
    supports_duplex BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brand(brand_id),
    FOREIGN KEY (max_paper_size_id) REFERENCES page_size(page_size_id),
    UNIQUE KEY unique_brand_model (brand_id, model_name),
    INDEX idx_brand (brand_id),
    INDEX idx_max_paper_size (max_paper_size_id)
);

CREATE TABLE printer_physical (
    printer_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    model_id CHAR(36) NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    campus_name VARCHAR(100) NOT NULL,
    building_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_date DATE,
    last_maintenance_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by CHAR(36),
    FOREIGN KEY (model_id) REFERENCES printer_model(model_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id),
    INDEX idx_model (model_id),
    INDEX idx_campus (campus_name),
    INDEX idx_building (building_name),
    INDEX idx_enabled (is_enabled)
);

-- Page Balance Management Tables
-- ============================================

CREATE TABLE page_size (
    page_size_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    size_name VARCHAR(20) NOT NULL UNIQUE,
    width_mm DECIMAL(6,2) NOT NULL,
    height_mm DECIMAL(6,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_size_name (size_name)
);

CREATE TABLE page_allocation (
    allocation_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    semester VARCHAR(20) NOT NULL,
    academic_year INT NOT NULL,
    page_type_id CHAR(36) NOT NULL,
    default_page_count INT NOT NULL,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by CHAR(36),
    UNIQUE KEY unique_semester_year_pagetype (semester, academic_year, page_type_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id),
    FOREIGN KEY (page_type_id) REFERENCES page_size(page_size_id),
    INDEX idx_semester (semester, academic_year),
    INDEX idx_page_type (page_type_id)
);



CREATE TABLE student_page_purchase (
    purchase_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36) NOT NULL,
    page_size_id CHAR(36) NOT NULL,
    quantity INT NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status ENUM('pending', 'completed', 'failed', 'refunded') NOT NULL DEFAULT 'pending',
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (page_size_id) REFERENCES page_size(page_size_id),
    INDEX idx_student_purchase (student_id),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_payment_status (payment_status),
    INDEX idx_page_size (page_size_id)
);

-- System Configuration Tables
-- ============================================

CREATE TABLE system_configuration (
    config_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by CHAR(36),
    FOREIGN KEY (updated_by) REFERENCES staff(staff_id),
    INDEX idx_config_key (config_key)
);

CREATE TABLE permitted_file_type (
    file_type_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    file_extension VARCHAR(10) NOT NULL UNIQUE,
    mime_type VARCHAR(100),
    description VARCHAR(100),
    is_permitted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by CHAR(36),
    FOREIGN KEY (updated_by) REFERENCES staff(staff_id),
    INDEX idx_extension (file_extension),
    INDEX idx_permitted (is_permitted)
);

-- Print Job Management Tables
-- ============================================

CREATE TABLE print_job (
    job_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    student_id CHAR(36) NOT NULL,
    printer_id CHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size_kb INT,
    paper_size_id CHAR(36) NOT NULL,
    page_orientation ENUM('portrait', 'landscape') NOT NULL DEFAULT 'portrait',
    print_side ENUM('one-sided', 'double-sided') NOT NULL DEFAULT 'one-sided',
    color_mode ENUM('color', 'grayscale', 'black-white') NOT NULL DEFAULT 'black-white',
    number_of_copy INT NOT NULL DEFAULT 1,
    print_status ENUM('queued', 'printing', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'queued',
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id),
    FOREIGN KEY (paper_size_id) REFERENCES page_size(page_size_id),
    INDEX idx_student_job (student_id),
    INDEX idx_printer_job (printer_id),
    INDEX idx_print_status (print_status),
    INDEX idx_created_at (created_at),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    INDEX idx_paper_size (paper_size_id)
);

CREATE TABLE print_job_page (
    page_record_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    job_id CHAR(36) NOT NULL,
    page_number INT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES print_job(job_id) ON DELETE CASCADE,
    INDEX idx_job_id (job_id),
    UNIQUE KEY unique_job_page (job_id, page_number)
);

-- Audit and Logging Tables
-- ============================================

CREATE TABLE printer_activity_log (
    log_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    printer_id CHAR(36) NOT NULL,
    action_type ENUM('added', 'enabled', 'disabled', 'updated', 'removed') NOT NULL,
    performed_by CHAR(36) NOT NULL,
    action_detail TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (printer_id) REFERENCES printer_physical(printer_id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES staff(staff_id),
    INDEX idx_printer_log (printer_id),
    INDEX idx_action_timestamp (action_timestamp)
);

CREATE TABLE system_audit_log (
    audit_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    table_name ENUM(
        'user', 'student', 'staff', 'brand', 'printer_model', 'printer_physical',
        'page_allocation', 'student_page_purchase',
        'system_configuration', 'permitted_file_type', 'print_job', 'print_job_page',
        'printer_activity_log', 'system_audit_log'
    ),
    record_id CHAR(36),
    previous_audit_id CHAR(36) COMMENT 'Reference to previous audit record for this same record_id, forming an audit chain',
    changed_field JSON COMMENT 'JSON object containing only the fields that changed: {"field_name": "new_value"}',
    ip_address VARCHAR(45),
    user_agent TEXT COMMENT 'Browser/application identifier string containing info about client software, OS, and device used to make the request',
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (previous_audit_id) REFERENCES system_audit_log(audit_id),
    INDEX idx_user_audit (user_id),
    INDEX idx_action_timestamp (action_timestamp),
    INDEX idx_table_name (table_name),
    INDEX idx_record_id (record_id),
    INDEX idx_previous_audit (previous_audit_id)
);

-- ============================================
-- Composite Indexes for Query Optimization
-- ============================================

CREATE INDEX idx_print_job_student_date ON print_job(student_id, created_at);
CREATE INDEX idx_print_job_printer_date ON print_job(printer_id, created_at);
CREATE INDEX idx_print_job_status_date ON print_job(print_status, created_at);

-- ============================================
-- Views for Common Queries and Reports
-- ============================================

-- View: Student print summary with balance
CREATE VIEW student_print_summary AS
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
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) * 2 FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) * 0.5 FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
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
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) * 2 FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) * 0.5 FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
        END * pj.number_of_copy
    ), 0) AS remaining_a4_page
FROM student s
JOIN user u ON s.user_id = u.user_id
JOIN class c ON s.class_id = c.class_id
JOIN major m ON c.major_id = m.major_id
JOIN department d ON m.department_id = d.department_id
JOIN faculty f ON d.faculty_id = f.faculty_id
JOIN academic_year ay ON c.academic_year_id = ay.academic_year_id
LEFT JOIN print_job pj ON s.student_id = pj.student_id AND pj.print_status = 'completed'
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
GROUP BY s.student_id, s.student_code, u.full_name, u.email, 
         c.class_name, m.major_name, d.department_name, f.faculty_name, ay.year_name;

-- View: Printer usage statistics
CREATE VIEW printer_usage_statistic AS
SELECT 
    pp.printer_id,
    b.brand_name,
    pm.model_name,
    pp.campus_name,
    pp.building_name,
    pp.room_number,
    pp.is_enabled,
    COUNT(DISTINCT pj.job_id) AS total_job,
    COUNT(DISTINCT pj.student_id) AS unique_student_count,
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
        END * pj.number_of_copy
    ), 0) AS total_page_printed,
    MAX(pj.end_time) AS last_print_time
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
LEFT JOIN print_job pj ON pp.printer_id = pj.printer_id AND pj.print_status = 'completed'
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
GROUP BY pp.printer_id, b.brand_name, pm.model_name, pp.campus_name, pp.building_name, pp.room_number, pp.is_enabled;

-- View: Monthly reports (automated)
CREATE VIEW monthly_report AS
SELECT 
    YEAR(pj.end_time) AS report_year,
    MONTH(pj.end_time) AS report_month,
    COUNT(DISTINCT pj.job_id) AS total_print_job,
    COUNT(DISTINCT pj.student_id) AS total_student_used,
    COUNT(DISTINCT pj.printer_id) AS total_printer_used,
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) * 2 FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) * 0.5 FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY YEAR(pj.end_time), MONTH(pj.end_time);

-- View: Yearly reports (automated)
CREATE VIEW yearly_report AS
SELECT 
    YEAR(pj.end_time) AS report_year,
    COUNT(DISTINCT pj.job_id) AS total_print_job,
    COUNT(DISTINCT pj.student_id) AS total_student_used,
    COUNT(DISTINCT pj.printer_id) AS total_printer_used,
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) * 2 FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) * 0.5 FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page,
    COALESCE(SUM(spp.amount_paid), 0) AS total_revenue
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN student s ON pj.student_id = s.student_id
LEFT JOIN student_page_purchase spp ON s.student_id = spp.student_id 
    AND spp.payment_status = 'completed'
    AND YEAR(spp.transaction_date) = YEAR(pj.end_time)
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY YEAR(pj.end_time);

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
    pp.campus_name,
    pp.building_name,
    pp.room_number,
    pj.print_status,
    pj.start_time,
    pj.end_time
FROM print_job pj
JOIN student s ON pj.student_id = s.student_id
JOIN user u ON s.user_id = u.user_id
JOIN class c ON s.class_id = c.class_id
JOIN major m ON c.major_id = m.major_id
JOIN department d ON m.department_id = d.department_id
JOIN faculty f ON d.faculty_id = f.faculty_id
JOIN printer_physical pp ON pj.printer_id = pp.printer_id
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
LEFT JOIN print_job_page pjp ON pj.job_id = pjp.job_id
GROUP BY pj.job_id, s.student_id, s.student_code, u.full_name, 
         c.class_name, m.major_name, d.department_name, f.faculty_name,
         pj.file_name, ps.size_name, pj.print_side, pj.color_mode, pj.number_of_copy,
         b.brand_name, pm.model_name, pp.campus_name, pp.building_name, 
         pp.room_number, pj.print_status, pj.start_time, pj.end_time;

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
    pp.campus_name,
    pp.building_name,
    pp.room_number,
    pp.installed_date,
    pp.last_maintenance_date,
    pp.is_enabled,
    CONCAT(pp.campus_name, ' - ', pp.building_name, ' - Room ', pp.room_number) AS full_location
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN page_size ps ON pm.max_paper_size_id = ps.page_size_id
WHERE pp.is_enabled = TRUE;

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
JOIN user u ON s.user_id = u.user_id
LEFT JOIN student_page_purchase spp ON s.student_id = spp.student_id
LEFT JOIN page_size ps ON spp.page_size_id = ps.page_size_id
GROUP BY s.student_id, s.student_code, u.full_name;

-- View: Daily printing activity
CREATE VIEW daily_printing_activity AS
SELECT 
    DATE(pj.end_time) AS print_date,
    COUNT(DISTINCT pj.job_id) AS total_job,
    COUNT(DISTINCT pj.student_id) AS unique_student,
    COUNT(DISTINCT pj.printer_id) AS printer_used,
    COALESCE(SUM(
        CASE 
            WHEN ps.size_name = 'A4' THEN (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A3' THEN (SELECT COUNT(*) * 2 FROM print_job_page WHERE job_id = pj.job_id)
            WHEN ps.size_name = 'A5' THEN (SELECT COUNT(*) * 0.5 FROM print_job_page WHERE job_id = pj.job_id)
            ELSE (SELECT COUNT(*) FROM print_job_page WHERE job_id = pj.job_id)
        END * pj.number_of_copy
    ), 0) AS total_a4_equivalent_page
FROM print_job pj
LEFT JOIN page_size ps ON pj.paper_size_id = ps.page_size_id
WHERE pj.print_status = 'completed' AND pj.end_time IS NOT NULL
GROUP BY DATE(pj.end_time);

-- View: Printer maintenance schedule
CREATE VIEW printer_maintenance_status AS
SELECT 
    pp.printer_id,
    b.brand_name,
    pm.model_name,
    pp.campus_name,
    pp.building_name,
    pp.room_number,
    pp.installed_date,
    pp.last_maintenance_date,
    DATEDIFF(CURDATE(), pp.last_maintenance_date) AS days_since_maintenance,
    COUNT(pj.job_id) AS job_count_since_maintenance
FROM printer_physical pp
JOIN printer_model pm ON pp.model_id = pm.model_id
JOIN brand b ON pm.brand_id = b.brand_id
LEFT JOIN print_job pj ON pp.printer_id = pj.printer_id 
    AND pj.end_time > pp.last_maintenance_date
WHERE pp.is_enabled = TRUE
GROUP BY pp.printer_id, b.brand_name, pm.model_name, pp.campus_name, 
         pp.building_name, pp.room_number, pp.installed_date, pp.last_maintenance_date;