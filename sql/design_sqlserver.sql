-- ============================================
-- HCMSIU Student Smart Printing Service (SSPS)
-- Database Schema - SQL Server Version
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
    password_salt VARCHAR(255) NOT NULL,
    user_type VARCHAR(10) NOT NULL CHECK (user_type IN ('student', 'staff')),
    phone_number VARCHAR(15),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
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
    serial_number VARCHAR(100) UNIQUE,
    campus_name VARCHAR(100) NOT NULL,
    building_name VARCHAR(100) NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    is_enabled BIT DEFAULT 1,
    installed_date DATE,
    last_maintenance_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    FOREIGN KEY (model_id) REFERENCES printer_model(model_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id)
);
CREATE INDEX idx_model ON printer_physical (model_id);
CREATE INDEX idx_campus ON printer_physical (campus_name);
CREATE INDEX idx_building ON printer_physical (building_name);
CREATE INDEX idx_enabled ON printer_physical (is_enabled);
GO

-- Page Balance Management Tables
-- ============================================

CREATE TABLE page_allocation (
    allocation_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    semester VARCHAR(20) NOT NULL,
    academic_year INT NOT NULL,
    page_type_id UNIQUEIDENTIFIER NOT NULL,
    default_page_count INT NOT NULL,
    allocation_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER,
    UNIQUE (semester, academic_year, page_type_id),
    FOREIGN KEY (created_by) REFERENCES staff(staff_id),
    FOREIGN KEY (page_type_id) REFERENCES page_size(page_size_id)
);
CREATE INDEX idx_semester ON page_allocation (semester, academic_year);
CREATE INDEX idx_page_type ON page_allocation (page_type_id);
GO

CREATE TABLE student_page_purchase (
    purchase_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    page_size_id UNIQUEIDENTIFIER NOT NULL,
    quantity INT NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'completed', 'failed', 'refunded')),
    transaction_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (page_size_id) REFERENCES page_size(page_size_id)
);
CREATE INDEX idx_student_purchase ON student_page_purchase (student_id);
CREATE INDEX idx_transaction_date ON student_page_purchase (transaction_date);
CREATE INDEX idx_payment_status ON student_page_purchase (payment_status);
CREATE INDEX idx_page_size ON student_page_purchase (page_size_id);
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

CREATE TABLE printer_activity_log (
    log_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    printer_id UNIQUEIDENTIFIER NOT NULL,
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('added', 'enabled', 'disabled', 'updated', 'removed')),
    performed_by UNIQUEIDENTIFIER NOT NULL,
    action_detail TEXT,
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
    table_name VARCHAR(50) CHECK (table_name IN (
        'user', 'student', 'staff', 'brand', 'printer_model', 'printer_physical',
        'page_allocation', 'student_page_purchase',
        'system_configuration', 'permitted_file_type', 'print_job', 'print_job_page',
        'printer_activity_log', 'system_audit_log'
    )),
    record_id UNIQUEIDENTIFIER,
    previous_audit_id UNIQUEIDENTIFIER, -- Reference to previous audit record for this same record_id, forming an audit chain
    changed_field NVARCHAR(MAX), -- JSON object containing only the fields that changed: {"field_name": "new_value"}
    ip_address VARCHAR(45),
    user_agent TEXT, -- Browser/application identifier string containing info about client software, OS, and device used to make the request
    action_timestamp DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES [user](user_id),
    FOREIGN KEY (previous_audit_id) REFERENCES system_audit_log(audit_id)
);
CREATE INDEX idx_user_audit ON system_audit_log (user_id);
CREATE INDEX idx_action_timestamp_audit ON system_audit_log (action_timestamp);
CREATE INDEX idx_table_name ON system_audit_log (table_name);
CREATE INDEX idx_record_id ON system_audit_log (record_id);
CREATE INDEX idx_previous_audit ON system_audit_log (previous_audit_id);
GO

-- ============================================
-- Composite Indexes for Query Optimization
-- ============================================

CREATE INDEX idx_print_job_student_date ON print_job(student_id, created_at);
CREATE INDEX idx_print_job_printer_date ON print_job(printer_id, created_at);
CREATE INDEX idx_print_job_status_date ON print_job(print_status, created_at);
GO