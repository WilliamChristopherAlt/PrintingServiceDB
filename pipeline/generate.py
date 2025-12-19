#!/usr/bin/env python3
"""
Smart Printing Service System (SSPS) Data Generator
==================================================
Generates comprehensive, realistic test data for the HCMIU Smart Printing Service database.
"""

import random
import string
import bcrypt
import uuid
import yaml
import os
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIGURATION - Update these paths as needed  
# ============================================================================
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE_PATH = os.path.join(script_dir, "specs.yaml")
MEDIA_FOLDER = os.path.join(script_dir, "..", "medias", "docs")
PROFILE_PICS_FOLDER = os.path.join(script_dir, "..", "medias", "profile_pics")
OUTPUT_SQL_FILE = os.path.join(script_dir, "..", "sql", "insert.sql")

# Supabase storage configuration
SUPABASE_BASE_URL = "https://ilzhoxyiftrpphhbwliz.supabase.co/storage/v1/object/public"
SUPABASE_BUCKET_PRINT_JOBS = "print_jobs_files"
SUPABASE_BUCKET_FLOOR_DIAGRAMS = "floor_diagrams"

delete_path = os.path.join(script_dir, "..", "sql", "delete.sql")
design_path = os.path.join(script_dir, "..", "sql", "design.sql")

BULK_INSERT_SIZE = 1000  # Number of rows per INSERT statement

INCLUDE_SCHEMA_RESET = True  # When True, prepend delete.sql and design.sql content to output
SKIP_USE_STATEMENT = True     # When True, omit the "USE database; GO" block (set to True for SQL Server versions that don't support USE)
SQL_SERVER_MODE = True        # When True, generate SQL Server compatible syntax

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_distribution(dist_data):
    """Parse distribution data in multiple formats."""
    if isinstance(dist_data, dict):
        return dist_data
    elif isinstance(dist_data, list):
        result = {}
        for item in dist_data:
            if isinstance(item, dict):
                result.update(item)
            else:
                result[str(item)] = 1
        return result
    else:
        raise ValueError(f"Unsupported distribution format: {type(dist_data)}")

def weighted_choice(options_dict):
    """Make a weighted random choice from a dictionary or parsed distribution."""
    if isinstance(options_dict, list):
        options_dict = parse_distribution(options_dict)
    
    choices = list(options_dict.keys())
    weights = list(options_dict.values())
    return random.choices(choices, weights=weights, k=1)[0]

def load_spec(spec_path):
    """Load the specification YAML file."""
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)
    
    # Process comma-separated strings in lists
    list_fields = ['first_names', 'last_names', 'phone_prefixes']
    for field in list_fields:
        if field in spec and isinstance(spec[field], str):
            spec[field] = [name.strip() for name in spec[field].split(',')]
    
    return spec

def get_media_files(folder_path):
    """Get list of media files from a folder."""
    if not os.path.exists(folder_path):
        print(f"Warning: Folder {folder_path} does not exist")
        return []
    
    files = []
    for file in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file)):
            files.append(file)
    
    return files

def generate_password_hash(password="123456"):
    """
    Generate a bcrypt password hash compatible with Spring's BCryptPasswordEncoder
    (default strength 10).
    """
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode(), salt).decode()

def generate_uuid():
    """Generate a UUID string for SQL Server.""" 
    if SQL_SERVER_MODE:
        # Return bare GUID string; BulkInsertHelper will add quotes
        return str(uuid.uuid4()).upper()
    else:
        return str(uuid.uuid4()).upper()

def random_date_in_range(start_days_ago, end_days_ago=0):
    """Generate a random date within a range of days ago."""
    start_date = datetime.now() - timedelta(days=start_days_ago)
    end_date = datetime.now() - timedelta(days=end_days_ago)
    time_between = end_date - start_date
    days_between = time_between.days
    if days_between <= 0:
        return start_date
    random_days = random.randrange(max(1, days_between))
    return start_date + timedelta(days=random_days)

def random_datetime_with_pattern(days_ago, hour_patterns):
    """Generate datetime with specific hour patterns."""
    date = random_date_in_range(days_ago)
    
    # Choose hour based on patterns
    if random.random() < 0.5:  # 50% peak hours
        hour = random.choice(hour_patterns.get('peak', [9, 10, 14, 15]))
    elif random.random() < 0.3:  # 30% normal hours  
        hour = random.choice(hour_patterns.get('normal', [8, 11, 16]))
    else:  # 20% low hours
        hour = random.choice(hour_patterns.get('low', [7, 17, 18]))
    
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    return date.replace(hour=hour, minute=minute, second=second)

def sql_escape(text):
    """Escape single quotes for SQL."""
    if text is None:
        return None
    return str(text).replace("'", "''")

def generate_student_code(prefix, start_number, index):
    """Generate student code in format S20210001."""
    return f"{prefix}{start_number + index}"

def generate_staff_code(prefix, start_number, index):
    """Generate staff code in format E20200001."""
    return f"{prefix}{start_number + index}"

def generate_email(name, domain, code=None):
    """Generate email address."""
    # Remove spaces and convert to lowercase
    name_part = name.lower().replace(" ", "")
    if code:
        return f"{name_part}.{code.lower()}@{domain}"
    else:
        return f"{name_part}@{domain}"

def generate_phone_number(prefixes):
    """Generate Vietnamese phone number."""
    prefix = random.choice(prefixes)
    remaining = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{remaining}"

def generate_serial_number():
    """Generate printer serial number."""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=2))
    number = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{number}"

def generate_document_name(templates, courses, file_ext):
    """Generate realistic document names."""
    template = random.choice(templates)
    
    # Replace placeholders
    if "{number}" in template:
        template = template.replace("{number}", str(random.randint(1, 20)))
    if "{course}" in template:
        template = template.replace("{course}", random.choice(courses))
    if "{subject}" in template:
        template = template.replace("{subject}", random.choice(courses))
    if "{name}" in template:
        template = template.replace("{name}", f"Project{random.randint(1, 5)}")
    if "{topic}" in template:
        template = template.replace("{topic}", random.choice(courses))
    if "{title}" in template:
        template = template.replace("{title}", random.choice(courses)[:10])
    if "{date}" in template:
        template = template.replace("{date}", datetime.now().strftime("%m%d"))
    
    return f"{template}{file_ext}"

# ============================================================================
# BULK INSERT HELPER
# ============================================================================

class BulkInsertHelper:
    """Helper class to manage bulk inserts."""
    
    def __init__(self, table_name, columns):
        self.table_name = table_name
        self.columns = columns
        self.rows = []
        self.statements = []
    
    def add_row(self, values):
        """Add a row to the bulk insert."""
        self.rows.append(values)
        
        if len(self.rows) >= BULK_INSERT_SIZE:
            self.flush()
    
    def flush(self):
        """Write accumulated rows as a bulk INSERT statement."""
        if not self.rows:
            return
        
        column_list = ", ".join(self.columns)
        
        # Handle reserved table names in SQL Server mode (e.g., [user])
        table_name_sql = self.table_name
        try:
            from __main__ import SQL_SERVER_MODE  # may not exist in some contexts
            sql_server_mode = SQL_SERVER_MODE
        except ImportError:
            # Fallback: use module-level variable if available
            sql_server_mode = 'SQL_SERVER_MODE' in globals() and globals()['SQL_SERVER_MODE']
        
        if sql_server_mode and self.table_name.lower() == "user":
            table_name_sql = "[user]"
        values_list = []
        
        for row in self.rows:
            formatted_values = []
            for value in row:
                if value is None:
                    formatted_values.append("NULL")
                elif isinstance(value, str):
                    formatted_values.append(f"'{sql_escape(value)}'")
                elif isinstance(value, bool):
                    formatted_values.append("1" if value else "0")
                elif isinstance(value, (date, datetime)):
                    # Format date/datetime as quoted string
                    if isinstance(value, datetime):
                        formatted_values.append(f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'")
                    else:
                        formatted_values.append(f"'{value.strftime('%Y-%m-%d')}'")
                else:
                    formatted_values.append(str(value))
            values_list.append(f"({', '.join(formatted_values)})")
        
        sql = f"INSERT INTO {table_name_sql} ({column_list}) VALUES\n"
        sql += ",\n".join(values_list)
        sql += ";"
        
        self.statements.append(sql)
        self.rows = []
    
    def get_statements(self):
        """Get all SQL statements and clear buffer."""
        self.flush()
        statements = self.statements
        self.statements = []
        return statements

# ============================================================================
# SQL GENERATOR CLASS
# ============================================================================

class PrintingServiceDataGenerator:
    def __init__(self, spec, media_files, profile_pics_files=None):
        self.spec = spec
        self.media_files = media_files
        self.profile_pics_files = profile_pics_files or []
        self.sql_statements = []
        
        # Data storage for relationships
        self.users = []
        self.students = []
        self.staff = []
        self.brands = []
        self.models = []
        self.buildings = []
        self.floors = []
        self.rooms = []
        self.printers = []
        self.print_jobs = []
        self.semesters = []
        
        # Balance and payment system data
        # Note: user_balance is now computed via view, not stored in table
        self.deposit_bonus_packages = []
        self.page_size_prices = []
        self.color_modes = []
        self.color_mode_prices = []
        self.page_discount_packages = []
        self.deposits = []
        self.semester_bonuses = []
        self.student_semester_bonuses = []
        self.payments = []
        self.refunds = []
        
        # Academic structure data
        self.faculties = []
        self.departments = []
        self.majors = []
        self.academic_years = []
        self.classes = []
        
        # Lookup mappings
        self.user_by_id = {}
        self.student_by_id = {}
        self.staff_by_id = {}
        self.printer_by_id = {}
        self.floor_by_id = {}
        self.room_by_id = {}
        
        # Floor templates
        script_dir = os.path.dirname(os.path.abspath(__file__))
        maps_dir = os.path.join(script_dir, "..", "maps")
        self.floor_templates_dir = os.path.join(maps_dir, "specs")
        self.floors_diagrams_dir = os.path.join(maps_dir, "floors_diagrams")
        self.output_test_dir = os.path.join(maps_dir, "output_test")
        
        
        # Fund and supplier purchase data
        self.fund_sources = []
        self.supplier_purchases = []
        self.paper_purchase_items = []
        
        # System state
        self.current_academic_year = spec['current_academic_year']
        self.semester_names = spec['semester_names']
        
    def add_sql(self, statement):
        """Add a SQL statement."""
        self.sql_statements.append(statement)
    
    def is_test_student(self, email):
        """Check if an email belongs to a test student account."""
        test_student_emails = [
            "student.test@edu.vn",
            "phandienmanhthienk16@siu.edu.vn",
            "leanhtuank16@siu.edu.vn",
            "nguyenhongbaongock16@siu.edu.vn",
            "phanthanhthaituank16@siu.edu.vn",
            "lengocdangkhoak16@siu.edu.vn",
            "lyhieuvyk17@siu.edu.vn",
        ]
        return email in test_student_emails
    
    def is_test_staff(self, email):
        """Check if an email belongs to a test staff account."""
        return email == "staff.test@edu.vn"
    
    def is_test_account(self, email):
        """Check if an email belongs to any test account."""
        return self.is_test_student(email) or self.is_test_staff(email)
    
    def get_test_student_by_email(self, email):
        """Get test student data by email."""
        if not self.is_test_student(email):
            return None
        user = next((u for u in self.users if u['email'] == email), None)
        if not user:
            return None
        return next((s for s in self.students if s['user_id'] == user['user_id']), None)
    
    def generate_all_data(self):
        """Generate all database entries."""
        print("Generating user data...")
        self.generate_users()
        
        print("Generating academic structure...")
        self.generate_academic_structure()
        
        print("Generating student data...")
        self.generate_students()
        
        print("Generating staff data...")
        self.generate_staff()
        
        print("Generating page allocation system...")
        self.generate_page_allocation_system()
        
        print("Generating balance and payment system...")
        self.generate_balance_and_payment_system()
        
        print("Generating fund sources and supplier paper purchases...")
        self.generate_fund_and_supplier_purchases()
        
        print("Generating printer infrastructure...")
        print("  (This may take a moment for floor diagram generation...)")
        self.generate_printer_infrastructure()
        
        print("Generating system configuration...")
        self.generate_system_configuration()
        
        print("Generating print jobs...")
        self.generate_print_jobs()
        
        print("Generating activity logs...")
        self.generate_activity_logs()
        
        print("Generating audit logs...")
        self.generate_audit_logs()
        
        return "\n\n".join(self.sql_statements)
    
    def generate_users(self):
        """Generate user accounts."""
        self.add_sql("-- ============================================")
        self.add_sql("-- USER ACCOUNTS DATA")
        self.add_sql("-- ============================================")
        
        num_students = self.spec['num_students']
        num_staff = self.spec['num_staff']
        num_users = num_students + num_staff
        
        first_names = self.spec['first_names']
        last_names = self.spec['last_names']
        used_emails = set()
        
        # Generate shared password hash for all users
        shared_password_hash = generate_password_hash("123456")
        
        # Test account password hashes
        student_test_password_hash = generate_password_hash("SmartPrint@123")
        staff_test_password_hash = generate_password_hash("SmartPrint@123")
        
        bulk = BulkInsertHelper("user", [
            "user_id", "email", "full_name", "password_hash",
            "user_type", "phone_number", "date_of_birth", "gender",
            "citizen_id", "address", "profile_picture", "email_verified",
            "email_verification_code", "account_status", "created_at",
            "updated_at", "last_login_at", "is_active"
        ])
        
        phone_prefixes = self.spec['phone_prefixes']
        
        # Helper function to get random profile picture
        def get_profile_picture():
            if self.profile_pics_files:
                return random.choice(self.profile_pics_files)
            return None
        
        # Helper function to generate date of birth (18-25 years old for students, 25-60 for staff)
        def generate_date_of_birth(user_type):
            if user_type == 'student':
                age_years = random.randint(18, 25)
            else:
                age_years = random.randint(25, 60)
            birth_date = datetime.now() - timedelta(days=age_years * 365 + random.randint(0, 365))
            return birth_date.date()
        
        # Add test accounts first
        def name_from_email(email):
            local = email.split("@")[0]
            return local.replace('.', ' ').title()
        
        # Seeded student test accounts (all use SmartPrint@123)
        test_student_emails = [
            "student.test@edu.vn",
            "phandienmanhthienk16@siu.edu.vn",
            "leanhtuank16@siu.edu.vn",
            "nguyenhongbaongock16@siu.edu.vn",
            "phanthanhthaituank16@siu.edu.vn",
            "lengocdangkhoak16@siu.edu.vn",
            "lyhieuvyk17@siu.edu.vn",
        ]
        
        for test_email in test_student_emails:
            if test_email in used_emails:
                continue
            test_id = generate_uuid()
            used_emails.add(test_email)
            test_phone = generate_phone_number(phone_prefixes)
            test_created_at = random_date_in_range(365, 30)
            test_full_name = name_from_email(test_email)
            test_date_of_birth = generate_date_of_birth('student')
            test_gender = random.choice(['male', 'female'])
            test_citizen_id = f"{random.randint(100000000, 999999999)}"
            test_address = f"{random.randint(1, 999)} {random.choice(['Street', 'Avenue', 'Road'])}"
            test_profile_picture = get_profile_picture()
            test_email_verified = 1
            test_account_status = 'active'
            
            test_data = {
                'user_id': test_id,
                'email': test_email,
                'full_name': test_full_name,
                'user_type': 'student',
                'phone_number': test_phone,
                'created_at': test_created_at,
                'is_active': 1
            }
            self.users.append(test_data)
            self.user_by_id[test_id] = test_data
            
            bulk.add_row([
                test_id, test_email, test_full_name, student_test_password_hash,
                'student', test_phone, test_date_of_birth, test_gender,
                test_citizen_id, test_address, test_profile_picture, test_email_verified,
                None, test_account_status, test_created_at.strftime('%Y-%m-%d %H:%M:%S'),
                None, None, 1
            ])
        
        # Test staff account (password SmartPrint@123)
        test_staff_id = generate_uuid()
        test_staff_email = "staff.test@edu.vn"
        if test_staff_email not in used_emails:
            used_emails.add(test_staff_email)
        test_staff_phone = generate_phone_number(phone_prefixes)
        test_staff_created_at = random_date_in_range(365, 30)
        test_staff_date_of_birth = generate_date_of_birth('staff')
        test_staff_gender = random.choice(['male', 'female'])
        test_staff_citizen_id = f"{random.randint(100000000, 999999999)}"
        test_staff_address = f"{random.randint(1, 999)} {random.choice(['Street', 'Avenue', 'Road'])}"
        test_staff_profile_picture = get_profile_picture()
        test_staff_email_verified = 1
        test_staff_account_status = 'active'
        
        test_staff_data = {
            'user_id': test_staff_id,
            'email': test_staff_email,
            'full_name': 'Test Staff',
            'user_type': 'staff',
            'phone_number': test_staff_phone,
            'created_at': test_staff_created_at,
            'is_active': 1
        }
        self.users.append(test_staff_data)
        self.user_by_id[test_staff_id] = test_staff_data
        
        bulk.add_row([
            test_staff_id, test_staff_email, 'Test Staff', staff_test_password_hash,
            'staff', test_staff_phone, test_staff_date_of_birth, test_staff_gender,
            test_staff_citizen_id, test_staff_address, test_staff_profile_picture, test_staff_email_verified,
            None, test_staff_account_status, test_staff_created_at.strftime('%Y-%m-%d %H:%M:%S'),
            None, None, 1
        ])
        
        # Generate regular users
        for i in range(num_users):
            user_id = generate_uuid()
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            
            # Determine user type
            if i < num_students:
                user_type = 'student'
                email_domain = random.choice(self.spec['student_email_domains'])
            else:
                user_type = 'staff'
                email_domain = random.choice(self.spec['staff_email_domains'])
            
            # Ensure email uniqueness to satisfy UNIQUE(email) constraint
            base_email = generate_email(full_name, email_domain)
            email = base_email
            suffix = 1
            while email in used_emails:
                email = f"{base_email.split('@')[0]}{suffix}@{base_email.split('@')[1]}"
                suffix += 1
            used_emails.add(email)
            phone = generate_phone_number(phone_prefixes)
            created_at = random_date_in_range(730, 30)  # 2 years to 1 month ago
            is_active = 1  # All users are active now
            date_of_birth = generate_date_of_birth(user_type)
            gender = random.choice(['male', 'female'])
            citizen_id = f"{random.randint(100000000, 999999999)}"
            address = f"{random.randint(1, 999)} {random.choice(['Street', 'Avenue', 'Road'])}"
            profile_picture = get_profile_picture()
            email_verified = random.choice([0, 1])  # Some verified, some not
            email_verification_code = None if email_verified else f"VERIFY_{random.randint(100000, 999999)}"
            account_status = 'active'  # All active for now
            
            user_data = {
                'user_id': user_id,
                'email': email,
                'full_name': full_name,
                'user_type': user_type,
                'phone_number': phone,
                'created_at': created_at,
                'is_active': is_active
            }
            
            self.users.append(user_data)
            self.user_by_id[user_id] = user_data
            
            bulk.add_row([
                user_id, email, full_name, shared_password_hash,
                user_type, phone, date_of_birth, gender,
                citizen_id, address, profile_picture, email_verified,
                email_verification_code, account_status, created_at.strftime('%Y-%m-%d %H:%M:%S'),
                None, None, is_active
            ])
        
        for stmt in bulk.get_statements():
            self.add_sql(stmt)
    
    def generate_academic_structure(self):
        """Generate academic structure: faculties, departments, majors, academic years, classes."""
        self.add_sql("-- ============================================")
        self.add_sql("-- ACADEMIC STRUCTURE DATA")
        self.add_sql("-- ============================================")
        
        # Generate Faculties
        bulk_faculties = BulkInsertHelper("faculty", [
            "faculty_id", "faculty_name", "faculty_code", "description", 
            "established_date", "created_at"
        ])
        
        faculties_config = self.spec['faculties']
        
        for faculty_config in faculties_config:
            faculty_id = generate_uuid()
            created_at = random_date_in_range(365 * 30, 365 * 10)  # 10-30 years ago
            
            faculty_data = {
                'faculty_id': faculty_id,
                'name': faculty_config['name'],
                'code': faculty_config['code'],
                'departments': faculty_config['departments']
            }
            
            self.faculties.append(faculty_data)
            
            bulk_faculties.add_row([
                faculty_id, faculty_config['name'], faculty_config['code'],
                faculty_config['description'], faculty_config['established_date'],
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_faculties.get_statements():
            self.add_sql(stmt)
        
        # Generate Departments
        bulk_departments = BulkInsertHelper("department", [
            "department_id", "faculty_id", "department_name", "department_code",
            "description", "established_date", "created_at"
        ])
        
        for faculty in self.faculties:
            for dept_config in faculty['departments']:
                department_id = generate_uuid()
                created_at = random_date_in_range(365 * 25, 365 * 5)
                
                dept_data = {
                    'department_id': department_id,
                    'faculty_id': faculty['faculty_id'],
                    'name': dept_config['name'],
                    'code': dept_config['code'],
                    'majors': dept_config['majors']
                }
                
                self.departments.append(dept_data)
                
                bulk_departments.add_row([
                    department_id, faculty['faculty_id'], dept_config['name'],
                    dept_config['code'], f"Department of {dept_config['name']}",
                    faculty_config['established_date'], created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_departments.get_statements():
            self.add_sql(stmt)
        
        # Generate Majors
        bulk_majors = BulkInsertHelper("major", [
            "major_id", "department_id", "major_name", "major_code", "degree_type",
            "duration_years", "description", "established_date", "created_at"
        ])
        
        for department in self.departments:
            for major_config in department['majors']:
                major_id = generate_uuid()
                created_at = random_date_in_range(365 * 20, 365 * 2)
                
                major_data = {
                    'major_id': major_id,
                    'department_id': department['department_id'],
                    'name': major_config['name'],
                    'code': major_config['code'],
                    'degree_type': major_config['degree_type'],
                    'duration_years': major_config['duration_years']
                }
                
                self.majors.append(major_data)
                
                bulk_majors.add_row([
                    major_id, department['department_id'], major_config['name'],
                    major_config['code'], major_config['degree_type'],
                    major_config['duration_years'], f"Major in {major_config['name']}",
                    "2000-01-01", created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_majors.get_statements():
            self.add_sql(stmt)
        
        # Generate Academic Years
        bulk_academic_years = BulkInsertHelper("academic_year", [
            "academic_year_id", "year_name", "start_date", "end_date", 
            "is_current", "created_at"
        ])
        
        academic_years_config = self.spec['academic_years']
        
        for year_config in academic_years_config:
            academic_year_id = generate_uuid()
            created_at = datetime.now()
            
            academic_year_data = {
                'academic_year_id': academic_year_id,
                'year_name': year_config['year_name'],
                'start_date': year_config['start_date'],
                'end_date': year_config['end_date'],
                'is_current': year_config['is_current']
            }
            
            self.academic_years.append(academic_year_data)
            
            bulk_academic_years.add_row([
                academic_year_id, year_config['year_name'], year_config['start_date'],
                year_config['end_date'], year_config['is_current'],
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_academic_years.get_statements():
            self.add_sql(stmt)
        
        # Generate Classes
        bulk_classes = BulkInsertHelper("class", [
            "class_id", "major_id", "academic_year_id", "class_name", "class_code",
            "year_level", "max_students", "created_at"
        ])
        
        classes_per_major_year = self.spec['classes_per_major_year']
        max_students_per_class = self.spec['max_students_per_class']
        
        for major in self.majors:
            for academic_year in self.academic_years:
                for year_level in range(1, major['duration_years'] + 1):
                    for class_num in range(1, classes_per_major_year + 1):
                        class_id = generate_uuid()
                        class_name = f"{major['code']}{year_level:02d}0{class_num}"
                        class_code = f"{major['code']}-{academic_year['year_name']}-Y{year_level}-{class_num:02d}"
                        created_at = datetime.now()
                        
                        class_data = {
                            'class_id': class_id,
                            'major_id': major['major_id'],
                            'academic_year_id': academic_year['academic_year_id'],
                            'class_name': class_name,
                            'year_level': year_level,
                            'max_students': max_students_per_class
                        }
                        
                        self.classes.append(class_data)
                        
                        bulk_classes.add_row([
                            class_id, major['major_id'], academic_year['academic_year_id'],
                            class_name, class_code, year_level, max_students_per_class,
                            created_at.strftime('%Y-%m-%d %H:%M:%S')
                        ])
        
        # Flush class INSERT statements
        for stmt in bulk_classes.get_statements():
            self.add_sql(stmt)
        
    def generate_students(self):
        """Generate student-specific data."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- STUDENT DATA")
        self.add_sql("-- ============================================")
        
        bulk = BulkInsertHelper("student", [
            "student_id", "user_id", "student_code", "class_id", 
            "enrollment_date", "graduation_date", "status"
        ])
        
        student_users = [user for user in self.users if user['user_type'] == 'student' and user['is_active']]
        students_per_class = self.spec['students_per_class']
        
        # Map specific test student emails to fixed student codes
        test_student_codes = {
            'student.test@edu.vn': 'TEST001',
            'phandienmanhthienk16@siu.edu.vn': 'TEST002',
            'leanhtuank16@siu.edu.vn': 'TEST003',
            'nguyenhongbaongock16@siu.edu.vn': 'TEST004',
            'phanthanhthaituank16@siu.edu.vn': 'TEST005',
            'lengocdangkhoak16@siu.edu.vn': 'TEST006',
            'lyhieuvyk17@siu.edu.vn': 'TEST007',
        }
        
        # Prioritize test students: move them to the front of the list
        test_student_users = [u for u in student_users if u['email'] in test_student_codes]
        regular_student_users = [u for u in student_users if u['email'] not in test_student_codes]
        student_users = test_student_users + regular_student_users
        
        student_index = 0
        
        # Find a suitable class for assignment (current/recent academic year)
        suitable_classes = [
            class_info for class_info in self.classes
            if any(ay['academic_year_id'] == class_info['academic_year_id'] and 
                  ay['year_name'] in ['2023-2024', '2024-2025'] 
                  for ay in self.academic_years)
        ]
        
        # Distribute students across classes
        for class_info in suitable_classes:
            # Assign students to this class
            class_size = min(students_per_class, len(student_users) - student_index)
            if class_size <= 0:
                break
                
            for i in range(class_size):
                if student_index >= len(student_users):
                    break
                    
                user = student_users[student_index]
                student_id = generate_uuid()
                
                # Check if this is one of the seeded test student accounts
                if user['email'] in test_student_codes:
                    student_code = test_student_codes[user['email']]
                else:
                    student_code = generate_student_code(
                        self.spec['student_code_prefix'],
                        self.spec['student_code_start'],
                        student_index
                    )
                
                # Enrollment date based on class year level
                enrollment_date = random_date_in_range(365 * class_info['year_level'], 365 * (class_info['year_level'] - 1))
                graduation_date = None  # Most students haven't graduated yet
                if random.random() < 0.05:  # 5% chance of being graduated
                    graduation_date = random_date_in_range(365, 1)
                
                student_data = {
                    'student_id': student_id,
                    'user_id': user['user_id'],
                    'student_code': student_code,
                    'class_id': class_info['class_id'],
                    'enrollment_date': enrollment_date,
                    'status': 'active'
                }
                
                self.students.append(student_data)
                self.student_by_id[student_id] = student_data
                
                bulk.add_row([
                    student_id, user['user_id'], student_code, class_info['class_id'],
                    enrollment_date.strftime('%Y-%m-%d'), graduation_date.strftime('%Y-%m-%d') if graduation_date else None,
                    'active'
                ])
                
                student_index += 1
        
        for stmt in bulk.get_statements():
            self.add_sql(stmt)
    
    def generate_staff(self):
        """Generate staff-specific data."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- STAFF DATA")
        self.add_sql("-- ============================================")
        
        bulk = BulkInsertHelper("staff", [
            "staff_id", "user_id", "employee_code", "position", "hire_date"
        ])
        
        staff_users = [user for user in self.users if user['user_type'] == 'staff' and user['is_active']]
        position_dist = self.spec['staff_positions']
        
        for i, user in enumerate(staff_users):
            staff_id = generate_uuid()
            employee_code = generate_staff_code(
                self.spec['staff_code_prefix'],
                self.spec['staff_code_start'],
                i
            )
            
            position = weighted_choice(position_dist)
            hire_date = random_date_in_range(1825, 90)  # 5 years to 3 months ago
            
            staff_data = {
                'staff_id': staff_id,
                'user_id': user['user_id'],
                'employee_code': employee_code,
                'position': position,
                'hire_date': hire_date
            }
            
            self.staff.append(staff_data)
            self.staff_by_id[staff_id] = staff_data
            
            bulk.add_row([
                staff_id, user['user_id'], employee_code, position,
                hire_date.strftime('%Y-%m-%d')
            ])
        
        for stmt in bulk.get_statements():
            self.add_sql(stmt)
    
    def generate_printer_infrastructure(self):
        """Generate printer brands, models, buildings, floors, rooms, and physical printers."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PRINTER INFRASTRUCTURE DATA")
        self.add_sql("-- ============================================")
        
        # Import floor generator
        try:
            import sys
            script_dir = os.path.dirname(os.path.abspath(__file__))
            maps_dir = os.path.join(script_dir, "..", "maps")
            maps_dir_abs = os.path.abspath(maps_dir)
            if maps_dir_abs not in sys.path:
                sys.path.insert(0, maps_dir_abs)
            from floor_generator import generate_floor_diagram, get_room_grid_coordinate, grid_to_image_coordinate
        except ImportError as e:
            print(f"Warning: Could not import floor_generator: {e}")
            import traceback
            traceback.print_exc()
            generate_floor_diagram = None
            get_room_grid_coordinate = None
            grid_to_image_coordinate = None
        
        # Generate brands
        bulk_brands = BulkInsertHelper("brand", [
            "brand_id", "brand_name", "country_of_origin", "website", "created_at"
        ])
        
        brands_config = self.spec['printer_brands']
        
        for brand_config in brands_config:
            brand_id = generate_uuid()
            created_at = random_date_in_range(1095, 365)  # 3 years to 1 year ago
            
            brand_data = {
                'brand_id': brand_id,
                'name': brand_config['name'],
                'country': brand_config['country'],
                'website': brand_config['website'],
                'models': brand_config['models']
            }
            
            self.brands.append(brand_data)
            
            bulk_brands.add_row([
                brand_id, brand_config['name'], brand_config['country'],
                brand_config['website'], created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_brands.get_statements():
            self.add_sql(stmt)
        
        # Generate models
        bulk_models = BulkInsertHelper("printer_model", [
            "model_id", "brand_id", "model_name", "description", "max_paper_size_id",
            "supports_color", "supports_duplex", "pages_per_second", "image_2d_url",
            "image_3d_url", "created_at"
        ])
        
        for brand in self.brands:
            for model_config in brand['models']:
                model_id = generate_uuid()
                description = f"{brand['name']} {model_config['name']} - Professional printing solution"
                created_at = random_date_in_range(1095, 365)
                
                # Find page size ID based on model's max paper size
                max_paper_size_id = next(
                    ps["page_size_id"] for ps in self.page_sizes 
                    if ps["size_name"] == model_config['max_paper_size']
                )
                
                # Generate pages_per_second (typical range: 0.2 to 2.0 pages/second)
                # Use value from config if available, otherwise generate realistic value
                if 'pages_per_second' in model_config:
                    pages_per_second = float(model_config['pages_per_second'])
                else:
                    # Generate based on printer type: color printers are typically slower
                    if model_config.get('supports_color', False):
                        pages_per_second = round(random.uniform(0.2, 0.8), 2)  # 0.2-0.8 pps for color
                    else:
                        pages_per_second = round(random.uniform(0.5, 2.0), 2)  # 0.5-2.0 pps for B&W
                
                # Generate image URLs - use from config if available, otherwise NULL
                image_2d_url = model_config.get('image_2d_url', None)
                image_3d_url = model_config.get('image_3d_url', None)
                
                model_data = {
                    'model_id': model_id,
                    'brand_id': brand['brand_id'],
                    'name': model_config['name'],
                    'max_paper_size_id': max_paper_size_id,
                    'supports_color': model_config['supports_color'],
                    'supports_duplex': model_config['supports_duplex'],
                    'pages_per_second': pages_per_second,
                    'image_2d_url': image_2d_url,
                    'image_3d_url': image_3d_url
                }
                
                self.models.append(model_data)
                
                bulk_models.add_row([
                    model_id, brand['brand_id'], model_config['name'], description,
                    max_paper_size_id, model_config['supports_color'],
                    model_config['supports_duplex'], pages_per_second,
                    image_2d_url, image_3d_url,
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_models.get_statements():
            self.add_sql(stmt)
        
        # Generate buildings (3 buildings)
        bulk_buildings = BulkInsertHelper("building", [
            "building_id", "building_code", "address", "campus_name", "created_at"
        ])
        
        # Create 3 buildings
        building_names = ["Main Academic Building", "Science & Technology Building", "Library & Research Center"]
        campus_name = "Main Campus"  # Default campus
        
        for building_name in building_names:
            building_id = generate_uuid()
            building_code = building_name[:10].upper().replace(' ', '').replace('&', '')
            address = f"{building_name}, {campus_name}"
            
            building_data = {
                'building_id': building_id,
                'building_code': building_code,
                'building_name': building_name,
                'campus_name': campus_name,
                'address': address
            }
            
            self.buildings.append(building_data)
            
            created_at = random_date_in_range(3650, 365)
            bulk_buildings.add_row([
                building_id,
                sql_escape(building_code),
                sql_escape(address),
                sql_escape(campus_name),
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_buildings.get_statements():
            self.add_sql(stmt)
        
        # Generate floors (5 floors per building)
        bulk_floors = BulkInsertHelper("floor", [
            "floor_id", "building_id", "floor_number", "file_url", "created_at"
        ])
        
        # Load floor templates
        template_files = [
            "floor_template_1.json",
            "floor_template_2.json",
            "floor_template_3.json",
            "floor_template_4.json",
            "floor_template_5.json"
        ]
        
        print(f"  Generating {len(self.buildings)} buildings with 5 floors each...")
        floor_count = 0
        total_floors = len(self.buildings) * 5
        
        # Create floor data structures first
        for building in self.buildings:
            for floor_num in range(1, 6):  # 5 floors (1-5)
                floor_count += 1
                floor_id = generate_uuid()
                
                # Select template (cycle through templates)
                template_idx = (floor_num - 1) % len(template_files)
                template_file = template_files[template_idx]
                template_path = os.path.join(self.floor_templates_dir, template_file)
                
                floor_data = {
                    'floor_id': floor_id,
                    'building_id': building['building_id'],
                    'building_code': building['building_code'],
                    'floor_number': floor_num,
                    'template_path': template_path,
                    'file_url': None,
                    'grid_to_pixel_scale': None
                }
                
                self.floors.append(floor_data)
                self.floor_by_id[floor_id] = floor_data
        
        # Generate rooms from floor templates
        print(f"  Generating rooms from {len(self.floors)} floors...")
        bulk_rooms = BulkInsertHelper("room", [
            "room_id", "floor_id", "room_code", "room_name", "room_type", "created_at"
        ])
        
        # Room type mapping from template to database
        room_type_mapping = {
            'lab': 'Lab',
            'classroom': 'Lecture Hall',
            'library': 'Library',
            'office': 'Office',
            'lounge': 'Lounge',
            'storage': 'Storage',
            'corridor': 'Corridor',
            'restroom': 'Restroom',
            'stairs': 'Stairs',
            'elevator': 'Elevator'
        }
        
        # Room name templates based on type (NO NUMBERS OR CODES)
        room_name_templates = {
            'Lab': ['Computer Lab', 'IT Lab', 'Programming Lab', 'Software Lab', 'Hardware Lab'],
            'Lecture Hall': ['Lecture Hall', 'Classroom', 'Hall', 'Auditorium'],
            'Library': ['Library', 'Reading Room', 'Study Area', 'Reference Section'],
            'Office': ['Office', 'Faculty Office', 'Staff Office', 'Administrative Office'],
            'Lounge': ['Student Lounge', 'Common Area', 'Recreation Room', 'Break Room'],
            'Storage': ['Storage Room', 'Supply Room', 'Equipment Storage'],
            'Restroom': ["Women's", "Men's"],
            'Stairs': ['Stairwell', 'Stairs'],
            'Elevator': ['Elevator']
        }
        
        # Printer-allowed room types
        printer_room_types = {'lab', 'classroom', 'library'}
        
        room_count = 0
        for floor in self.floors:
            # Load template
            try:
                with open(floor['template_path'], 'r', encoding='utf-8') as f:
                    template = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load template {floor['template_path']}: {e}")
                continue
            
            rooms_spec = template.get('rooms', [])
            room_counter = 1
            
            # Build room mapping for diagram generation (template room ID -> database room_code)
            room_mapping = {}
            
            # Track restrooms to ensure exactly one Men's and one Women's per floor
            restroom_mens_assigned = False
            restroom_womens_assigned = False
            
            for room_spec in rooms_spec:
                # Skip corridors, stairs, elevators, and unlabeled rooms
                if not room_spec.get('label') or room_spec.get('type') in ['corridor', 'stairs', 'elevator']:
                    continue
                
                room_id = generate_uuid()
                room_code = f"{floor['floor_number']}{room_counter:02d}"
                template_type = room_spec.get('type', 'office')
                room_type = room_type_mapping.get(template_type, 'Office')
                template_room_id = room_spec.get('id', '').lower()
                original_label = room_spec.get('label', '')
                
                # Generate room name based on type (NO NUMBERS OR CODES)
                room_name = None
                if room_type == 'Restroom':
                    # For restrooms, assign based on template ID or label - ensure exactly one of each
                    if 'restroom-m' in template_room_id or original_label == "Men's":
                        if restroom_mens_assigned:
                            # Skip duplicate men's restroom
                            continue
                        room_name = "Men's"
                        restroom_mens_assigned = True
                    elif 'restroom-w' in template_room_id or original_label == "Women's":
                        if restroom_womens_assigned:
                            # Skip duplicate women's restroom
                            continue
                        room_name = "Women's"
                        restroom_womens_assigned = True
                    else:
                        # Fallback: assign based on what's needed
                        if not restroom_mens_assigned:
                            room_name = "Men's"
                            restroom_mens_assigned = True
                        elif not restroom_womens_assigned:
                            room_name = "Women's"
                            restroom_womens_assigned = True
                        else:
                            # Both already assigned, skip this restroom
                            continue
                elif room_type in room_name_templates:
                    templates = room_name_templates[room_type]
                    room_name = random.choice(templates)
                else:
                    # Fallback: use room type only (no number)
                    room_name = room_type
                
                # Map template room ID and label to database room_name for diagram labels
                # IMPORTANT: Only use room_name (no codes or numbers) for diagrams
                template_room_id = room_spec.get('id', '')
                original_label = room_spec.get('label', '')
                
                # Always map by ID if available (diagrams will show room_name only)
                if template_room_id:
                    room_mapping[template_room_id] = room_name
                
                # Always map by original label (we know it exists because we skip rooms without labels)
                if original_label:
                    room_mapping[original_label] = room_name
                
                # DO NOT map by room_code - diagrams should only show names, not codes
                
                room_data = {
                    'room_id': room_id,
                    'floor_id': floor['floor_id'],
                    'room_code': room_code,
                    'room_name': room_name,
                    'room_type': room_type,
                    'template_type': template_type,
                    'room_spec': room_spec,
                    'allows_printer': template_type in printer_room_types,
                    'template_room_id': template_room_id
                }
                
                self.rooms.append(room_data)
                self.room_by_id[room_id] = room_data
                
                created_at = random_date_in_range(2190, 180)
                bulk_rooms.add_row([
                    room_id,
                    floor['floor_id'],
                    sql_escape(room_code),
                    sql_escape(room_name),
                    sql_escape(room_type),
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
                room_counter += 1
            
            # Generate floor diagram with room mappings (after rooms are created)
            # Skip PNG generation for speed - only generate SVG (much faster)
            if generate_floor_diagram:
                # Debug: print room mapping for troubleshooting
                if room_mapping:
                    print(f"    Room mapping for {floor['building_code']} F{floor['floor_number']}: {len(room_mapping)} rooms")
                try:
                    # Generate SVG only (fast) - PNG will be generated in batch afterward
                    diagram_filename, grid_to_pixel_scale = generate_floor_diagram(
                        floor['template_path'],
                        self.floors_diagrams_dir,
                        floor['building_code'],
                        floor['floor_number'],
                        room_mapping if room_mapping else {},
                        generate_png=False,  # Skip PNG during pipeline for speed
                        include_printers=False  # NO printers in floors_diagrams
                    )
                    # Generate full Supabase URL for floor diagram
                    if diagram_filename:
                        floor['file_url'] = f"{SUPABASE_BASE_URL}/{SUPABASE_BUCKET_FLOOR_DIAGRAMS}/{diagram_filename}"
                    else:
                        floor['file_url'] = None
                    floor['grid_to_pixel_scale'] = grid_to_pixel_scale
                    
                    # Also generate SVG WITH printers for output_test folder
                    try:
                        generate_floor_diagram(
                            floor['template_path'],
                            self.output_test_dir,
                            floor['building_code'],
                            floor['floor_number'],
                            room_mapping if room_mapping else {},
                            generate_png=False,  # Skip PNG during pipeline for speed
                            include_printers=True  # WITH printers in output_test
                        )
                    except Exception as e:
                        print(f"    Warning: Could not generate test diagram with printers for {floor['building_code']} F{floor['floor_number']}: {e}")
                    
                    if (room_count + 1) % 5 == 0 or (room_count + 1) == len(self.floors):
                        print(f"    Generated {room_count + 1}/{len(self.floors)} floor diagrams...")
                except Exception as e:
                    print(f"    Warning: Could not generate floor diagram for {floor['building_code']} F{floor['floor_number']}: {e}")
            
            room_count += 1
        
        # IMPORTANT: Insert floors BEFORE rooms (rooms have FK to floors)
        # Now generate floor SQL with diagram filenames (after diagrams are generated)
        print(f"  Generating floor SQL with diagram filenames...")
        for floor in self.floors:
            created_at = random_date_in_range(2190, 180)
            bulk_floors.add_row([
                floor['floor_id'],
                floor['building_id'],
                floor['floor_number'],
                sql_escape(floor['file_url']) if floor.get('file_url') else None,
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Insert floors FIRST (before rooms)
        for stmt in bulk_floors.get_statements():
            self.add_sql(stmt)
        
        # Insert rooms AFTER floors (rooms reference floors via FK)
        for stmt in bulk_rooms.get_statements():
            self.add_sql(stmt)
        
        # Generate physical printers from specs (only in lab, lecture hall, library, office)
        bulk_printers = BulkInsertHelper("printer_physical", [
            "printer_id", "model_id", "room_id", "serial_number", "printer_pixel_coordinate",
            "is_enabled", "status", "printing_status", "installed_date", "last_maintenance_date",
            "created_at", "created_by"
        ])
        
        # Get a random staff member as creator
        creator_staff = random.choice(self.staff) if self.staff else None
        
        # Map room template IDs to database room IDs for printer assignment
        room_template_to_db = {}  # Maps template room ID -> database room data
        for room in self.rooms:
            template_id = room.get('template_room_id', '').lower()
            if template_id:
                room_template_to_db[template_id] = room
        
        status_options = ['idle', 'idle', 'idle', 'idle', 'idle', 'printing', 'maintained', 'unplugged']
        printing_status_options = ['printing', 'paper_jam', 'low_toner', 'out_of_paper', 'network_error', 'error']
        
        # Generate printers from specs for each floor
        for floor in self.floors:
            # Load template to get printers
            try:
                with open(floor['template_path'], 'r', encoding='utf-8') as f:
                    template = json.load(f)
            except Exception as e:
                continue
            
            printers_spec = template.get('printers', [])
            
            for printer_spec in printers_spec:
                # Find the room by template ID
                room_template_id = printer_spec.get('room', '').lower()
                room = room_template_to_db.get(room_template_id)
                
                if not room:
                    continue  # Room not found, skip this printer
                
                printer_id = generate_uuid()
                model = random.choice(self.models)
                
                serial_number = generate_serial_number()
                installed_date = random_date_in_range(1095, 30)
                last_maintenance = random_date_in_range(90, 0)
                created_at = installed_date
                is_enabled = random.choice([True, True, True, False])  # 75% enabled
                
                # Get printer grid coordinates from spec
                pixel_coordinate = None
                if get_room_grid_coordinate and grid_to_image_coordinate and room.get('room_spec'):
                    grid_rx = printer_spec.get('grid_rx', 0.15)  # Default near left wall
                    grid_ry = printer_spec.get('grid_ry', 0.2)   # Default near top wall
                    grid_x, grid_y = get_room_grid_coordinate(room['room_spec'], grid_rx, grid_ry)
                    
                    # Get floor to get grid_to_pixel_scale
                    floor_obj = self.floor_by_id.get(room['floor_id'])
                    if floor_obj and floor_obj.get('grid_to_pixel_scale'):
                        pixel_x, pixel_y = grid_to_image_coordinate(grid_x, grid_y, floor_obj['grid_to_pixel_scale'])
                        # Store as JSON: {"grid": [x, y], "pixel": [x, y]}
                        import json as json_module
                        pixel_coordinate = json_module.dumps({
                            "grid": [round(grid_x, 2), round(grid_y, 2)],
                            "pixel": [pixel_x, pixel_y]
                        })
                
                # Generate status
                if not is_enabled:
                    status = random.choice(['unplugged', 'maintained'])
                else:
                    status = random.choice(status_options)
                
                # Generate printing_status
                printing_status = None
                if status == 'printing':
                    if random.random() < 0.85:
                        printing_status = 'printing'
                    else:
                        printing_status = random.choice(printing_status_options)
                
                printer_data = {
                    'printer_id': printer_id,
                    'model_id': model['model_id'],
                    'room_id': room['room_id'],
                    'pixel_coordinate': pixel_coordinate,
                    'is_enabled': is_enabled,
                    'status': status,
                    'printing_status': printing_status,
                    'printer_spec': printer_spec  # Store spec for diagram generation
                }
                
                self.printers.append(printer_data)
                self.printer_by_id[printer_id] = printer_data
                
                bulk_printers.add_row([
                    printer_id, model['model_id'], room['room_id'], serial_number,
                    sql_escape(pixel_coordinate) if pixel_coordinate else None,
                    is_enabled, status, printing_status,
                    installed_date.strftime('%Y-%m-%d'),
                    last_maintenance.strftime('%Y-%m-%d'),
                    created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    creator_staff['staff_id'] if creator_staff else None
                ])
        
        for stmt in bulk_printers.get_statements():
            self.add_sql(stmt)
    
    def generate_page_allocation_system(self):
        """Generate page sizes and pricing configuration."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PAGE SIZES AND PRICING CONFIGURATION DATA")
        self.add_sql("-- ============================================")
        
        # Generate page sizes
        bulk_page_sizes = BulkInsertHelper("page_size", [
            "page_size_id", "size_name", "width_mm", "height_mm", "created_at"
        ])
        
        page_sizes_data = [
            {"name": "A3", "width": 297.0, "height": 420.0},
            {"name": "A4", "width": 210.0, "height": 297.0},
            {"name": "A5", "width": 148.0, "height": 210.0}
        ]
        
        self.page_sizes = []  # Store for use in other methods
        created_at = random_date_in_range(365, 30)
        
        for page_data in page_sizes_data:
            page_size_id = generate_uuid()
            
            self.page_sizes.append({
                "page_size_id": page_size_id,
                "size_name": page_data["name"],
                "width_mm": page_data["width"],
                "height_mm": page_data["height"]
            })
            
            bulk_page_sizes.add_row([
                page_size_id, page_data["name"], page_data["width"], 
                page_data["height"], created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_page_sizes.get_statements():
            self.add_sql(stmt)
        
        # Generate semester records (Fall, Spring, Summer for each academic year)
        bulk_semesters = BulkInsertHelper("semester", [
            "semester_id", "academic_year_id", "term_name", "start_date", "end_date", "created_at"
        ])
        
        term_order = [
            ("fall", 9, 12),   # Sept - Dec of start year
            ("spring", 1, 5),  # Jan - May of next year
            ("summer", 6, 8)   # Jun - Aug of next year
        ]
        
        for ay in self.academic_years:
            year_name = ay['year_name']
            # Expect formats like "2023-2024"; fallback to start_date year
            try:
                start_year = int(year_name.split('-')[0])
            except Exception:
                start_year = datetime.strptime(ay['start_date'], "%Y-%m-%d").year
            
            for term_name, start_month, end_month in term_order:
                if term_name == "fall":
                    term_year_start = start_year
                    term_year_end = start_year
                else:
                    term_year_start = start_year + 1
                    term_year_end = start_year + 1
                
                start_date = datetime(term_year_start, start_month, 1)
                # End date = last day of end_month
                if end_month in [1,3,5,7,8,10,12]:
                    end_day = 31
                elif end_month == 2:
                    end_day = 28
                else:
                    end_day = 30
                end_date = datetime(term_year_end, end_month, end_day)
                
                semester_id = generate_uuid()
                self.semesters.append({
                    "semester_id": semester_id,
                    "academic_year_id": ay['academic_year_id'],
                    "term_name": term_name,
                    "start_date": start_date,
                    "end_date": end_date
                })
                
                bulk_semesters.add_row([
                    semester_id,
                    ay['academic_year_id'],
                    term_name,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_semesters.get_statements():
            self.add_sql(stmt)
        
        # Generate page size prices
        self.add_sql("\n-- Page Size Prices")
        bulk_page_prices = BulkInsertHelper("page_size_price", [
            "price_id", "page_size_id", "page_price", "is_active", "created_at", "updated_at"
        ])
        
        # Base prices: A4 = $0.20, A3 = $0.40 (2x A4), A5 = $0.10 (0.5x A4)
        # Note: A4=0.5*A3, A3=2*A5 conversion is data only, prices are independent
        base_price_a4 = 0.20
        page_prices = {
            "A4": base_price_a4,
            "A3": base_price_a4 * 2.0,  # $0.40
            "A5": base_price_a4 * 0.5   # $0.10
        }
        
        created_at = random_date_in_range(365, 30)
        for page_size in self.page_sizes:
            price_id = generate_uuid()
            size_name = page_size["size_name"]
            page_price = page_prices.get(size_name, base_price_a4)
            
            self.page_size_prices.append({
                'price_id': price_id,
                'page_size_id': page_size["page_size_id"],
                'page_price': page_price,
                'is_active': True
            })
            
            bulk_page_prices.add_row([
                price_id,
                page_size["page_size_id"],
                page_price,
                1,  # is_active
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_page_prices.get_statements():
            self.add_sql(stmt)
        
        # Generate color modes first
        self.add_sql("\n-- Color Modes")
        bulk_color_modes = BulkInsertHelper("color_mode", [
            "color_mode_id", "color_mode_name", "description", "created_at"
        ])
        
        color_modes_data = [
            {"name": "black-white", "desc": "Black and white printing"},
            {"name": "grayscale", "desc": "Grayscale printing"},
            {"name": "color", "desc": "Color printing"}
        ]
        
        created_at = random_date_in_range(365, 30)
        
        for mode_data in color_modes_data:
            color_mode_id = generate_uuid()
            
            self.color_modes.append({
                'color_mode_id': color_mode_id,
                'color_mode_name': mode_data["name"]
            })
            
            bulk_color_modes.add_row([
                color_mode_id,
                mode_data["name"],
                mode_data["desc"],
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_color_modes.get_statements():
            self.add_sql(stmt)
        
        # Generate color mode prices
        self.add_sql("\n-- Color Mode Prices")
        bulk_print_prices = BulkInsertHelper("color_mode_price", [
            "setting_id", "color_mode_id", "price_per_page", "is_active", "created_at", "updated_at"
        ])
        
        # Color mode prices per page (absolute prices in dollars)
        color_price_settings = [
            {"mode": "black-white", "price": 0.10},
            {"mode": "grayscale", "price": 0.15},
            {"mode": "color", "price": 0.30}
        ]
        
        for price_setting in color_price_settings:
            # Find matching color_mode
            matching_color_mode = next(
                (cm for cm in self.color_modes if cm['color_mode_name'] == price_setting["mode"]),
                None
            )
            if not matching_color_mode:
                raise ValueError(f"No color_mode found for: {price_setting['mode']}")
            
            setting_id = generate_uuid()
                
            self.color_mode_prices.append({
                'setting_id': setting_id,
                'color_mode_id': matching_color_mode['color_mode_id'],
                'color_mode_name': matching_color_mode['color_mode_name'],  # Keep for lookup
                'price_per_page': price_setting["price"],
                'is_active': True
                })
                
            bulk_print_prices.add_row([
                setting_id,
                matching_color_mode['color_mode_id'],
                price_setting["price"],
                1,  # is_active
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_print_prices.get_statements():
            self.add_sql(stmt)
        
        # Generate page discount packages
        self.add_sql("\n-- Page Discount Packages")
        bulk_page_discounts = BulkInsertHelper("page_discount_package", [
            "package_id", "min_pages", "discount_percentage", "package_name", "description", "is_active", "created_at", "updated_at"
        ])
        
        # Discount packages: 50 pages = 0%, 100 pages = 10% off, 200 pages = 12.5% off, 500 pages = 20% off
        discount_packages = [
            {"min_pages": 50, "discount": 0.0, "name": "50 pages", "desc": "50 pages: no discount"},
            {"min_pages": 100, "discount": 0.10, "name": "100 pages", "desc": "100 pages: 10% discount"},
            {"min_pages": 200, "discount": 0.125, "name": "200 pages", "desc": "200 pages: 12.5% discount"},
            {"min_pages": 500, "discount": 0.20, "name": "500 pages", "desc": "500 pages: 20% discount"}
        ]
        
        for pkg in discount_packages:
            package_id = generate_uuid()
            
            self.page_discount_packages.append({
                'package_id': package_id,
                'min_pages': pkg["min_pages"],
                'discount_percentage': pkg["discount"],
                'is_active': True
            })
            
            bulk_page_discounts.add_row([
                package_id,
                pkg["min_pages"],
                pkg["discount"],  # Already 0-1 range
                pkg["name"],
                pkg["desc"],
                1,  # is_active
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_page_discounts.get_statements():
            self.add_sql(stmt)
    
    def generate_balance_and_payment_system(self):
        """Generate balance and payment system data including deposits, bonuses, and payments."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- BALANCE AND PAYMENT SYSTEM DATA")
        self.add_sql("-- ============================================")
        
        # 1. Generate deposit bonus packages
        self.add_sql("\n-- Deposit Bonus Packages")
        bulk_bonus_packages = BulkInsertHelper("deposit_bonus_package", [
            "package_id", "amount_cap", "bonus_percentage", "package_name", "description", "is_active", "created_at", "updated_at"
        ])
        
        # Deposit bonus packages (VND-based), stored as amount_cap (min deposit) and bonus_percentage (0-1 range)
        # These match the business spec and are emitted verbatim into insert.sql
        bonus_packages = [
            {
                "amount_cap": 50000.00,
                "bonus_percentage": 0.00,
                "name": "Gói Cơ Bản",
                "desc": "BASIC - Nạp 50,000₫, bonus 0₫ (0%), tổng nhận 50,000₫."
            },
            {
                "amount_cap": 100000.00,
                "bonus_percentage": 0.10,
                "name": "Gói Tiết Kiệm",
                "desc": "SAVE_10 - Nạp 100,000₫, bonus 10,000₫ (10%), tổng nhận 110,000₫."
            },
            {
                "amount_cap": 200000.00,
                "bonus_percentage": 0.25,
                "name": "Gói Giáng Sinh",
                "desc": "XMAS_25 - Nạp 200,000₫, bonus 50,000₫ (25%), tổng nhận 250,000₫."
            },
            {
                "amount_cap": 500000.00,
                "bonus_percentage": 0.30,
                "name": "Gói Siêu Tiết Kiệm",
                "desc": "SAVE_30 - Nạp 500,000₫, bonus 150,000₫ (30%), tổng nhận 650,000₫."
            },
        ]
        
        for pkg in bonus_packages:
            package_id = generate_uuid()
            created_at = random_date_in_range(365, 30)
            
            self.deposit_bonus_packages.append({
                'package_id': package_id,
                'amount_cap': pkg['amount_cap'],
                'bonus_percentage': pkg['bonus_percentage']
            })
            
            bulk_bonus_packages.add_row([
                package_id,
                pkg['amount_cap'],
                pkg['bonus_percentage'],
                pkg['name'],
                pkg['desc'],
                1,  # is_active
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_bonus_packages.get_statements():
            self.add_sql(stmt)
        
        # 2. Generate semester bonuses
        # Note: User balances are computed dynamically via student_balance_view, no table needed
        self.add_sql("\n-- Semester Bonuses")
        bulk_semester_bonuses = BulkInsertHelper("semester_bonus", [
            "bonus_id", "semester_id", "bonus_amount", "description", "created_at", "created_by"
        ])
        
        creator_staff = random.choice(self.staff) if self.staff else None
        default_semester_bonus = 5.00  # $5 per semester
        
        for semester in self.semesters:
            bonus_id = generate_uuid()
            bonus_amount = default_semester_bonus
            created_at = semester['start_date']
            if isinstance(created_at, str):
                created_at = datetime.strptime(created_at, '%Y-%m-%d')
            
            self.semester_bonuses.append({
                'bonus_id': bonus_id,
                'semester_id': semester['semester_id'],
                'bonus_amount': bonus_amount
            })
            
            bulk_semester_bonuses.add_row([
                bonus_id,
                semester['semester_id'],
                bonus_amount,
                f"Semester bonus for {semester['term_name']} semester",
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                creator_staff['staff_id'] if creator_staff else None
            ])
        
        for stmt in bulk_semester_bonuses.get_statements():
            self.add_sql(stmt)
        
        # 4. Generate student semester bonuses (only for students enrolled before semester start)
        self.add_sql("\n-- Student Semester Bonuses")
        bulk_student_semester_bonuses = BulkInsertHelper("student_semester_bonus", [
            "student_bonus_id", "student_id", "semester_bonus_id", "semester_id", "received", "received_date", "created_at"
        ])
        
        # Identify test students for guaranteed semester bonuses
        test_student_emails = [
            "student.test@edu.vn",
            "phandienmanhthienk16@siu.edu.vn",
            "leanhtuank16@siu.edu.vn",
            "nguyenhongbaongock16@siu.edu.vn",
            "phanthanhthaituank16@siu.edu.vn",
            "lengocdangkhoak16@siu.edu.vn",
            "lyhieuvyk17@siu.edu.vn",
        ]
        test_student_ids = set()
        for email in test_student_emails:
            user = next((u for u in self.users if u['email'] == email), None)
            if user:
                student = next((s for s in self.students if s['user_id'] == user['user_id']), None)
                if student:
                    test_student_ids.add(student['student_id'])
        
        for student in self.students:
            enrollment_date = student.get('enrollment_date')
            if not enrollment_date:
                continue
            if isinstance(enrollment_date, str):
                enrollment_date = datetime.strptime(enrollment_date, '%Y-%m-%d').date()
            elif isinstance(enrollment_date, datetime):
                enrollment_date = enrollment_date.date()
            
            is_test_account = student['student_id'] in test_student_ids
            
            for semester_bonus in self.semester_bonuses:
                semester = next((s for s in self.semesters if s['semester_id'] == semester_bonus['semester_id']), None)
                if not semester:
                    continue
                
                semester_start = semester['start_date']
                if isinstance(semester_start, str):
                    semester_start = datetime.strptime(semester_start, '%Y-%m-%d').date()
                elif isinstance(semester_start, datetime):
                    semester_start = semester_start.date()
                
                # Only give bonus if student was enrolled before semester start
                if enrollment_date <= semester_start:
                    student_bonus_id = generate_uuid()
                    # Test accounts always receive bonus, regular students 80% chance
                    received = True if is_test_account else (random.random() < 0.8)
                    received_date = semester_start + timedelta(days=random.randint(0, 30)) if received else None
                    
                    self.student_semester_bonuses.append({
                        'student_bonus_id': student_bonus_id,
                        'student_id': student['student_id'],
                        'semester_bonus_id': semester_bonus['bonus_id'],
                        'semester_id': semester['semester_id'],
                        'received': received
                    })
                    
                    bulk_student_semester_bonuses.add_row([
                        student_bonus_id,
                    student['student_id'],
                        semester_bonus['bonus_id'],
                        semester['semester_id'],
                        1 if received else 0,
                        received_date.strftime('%Y-%m-%d') if received_date else None,
                        semester_start.strftime('%Y-%m-%d %H:%M:%S')
                    ])
        
        for stmt in bulk_student_semester_bonuses.get_statements():
            self.add_sql(stmt)
    
        # 5. Generate deposits (students depositing money)
        self.add_sql("\n-- Deposits")
        bulk_deposits = BulkInsertHelper("deposit", [
            "deposit_id", "student_id", "deposit_amount", "bonus_amount", "total_credited",
            "deposit_bonus_package_id", "payment_method", "payment_reference", "payment_status", "transaction_date"
        ])
        
        # Get payment methods - ensure it's a list
        payment_methods_raw = self.spec.get('payment_methods', ['credit_card', 'debit_card', 'bank_transfer', 'e_wallet'])
        if isinstance(payment_methods_raw, dict):
            payment_methods = list(payment_methods_raw.keys())
        elif isinstance(payment_methods_raw, list):
            payment_methods = payment_methods_raw
        else:
            payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'e_wallet']
        deposit_rate = 0.3  # 30% of students make deposits
        
        # Track balances for payment logic (will be computed after deposits are generated)
        # Note: This is only for payment generation logic, actual balance is computed via view
        student_balance_map = {}
        
        # Identify test students to ensure they get guaranteed deposits
        test_student_emails = [
            "student.test@edu.vn",
            "phandienmanhthienk16@siu.edu.vn",
            "leanhtuank16@siu.edu.vn",
            "nguyenhongbaongock16@siu.edu.vn",
            "phanthanhthaituank16@siu.edu.vn",
            "lengocdangkhoak16@siu.edu.vn",
            "lyhieuvyk17@siu.edu.vn",
        ]
        test_student_ids = set()
        for email in test_student_emails:
            user = next((u for u in self.users if u['email'] == email), None)
            if user:
                student = next((s for s in self.students if s['user_id'] == user['user_id']), None)
                if student:
                    test_student_ids.add(student['student_id'])
        
        for student in self.students:
            is_test_account = student['student_id'] in test_student_ids
            # Test accounts always get deposits, regular students have 30% chance
            should_generate_deposit = True if is_test_account else (random.random() < deposit_rate)
            
            if should_generate_deposit:
                # Test accounts get exactly 20 deposits, regular students get 1-3
                num_deposits = 20 if is_test_account else random.randint(1, 3)
                
                for _ in range(num_deposits):
                    deposit_id = generate_uuid()
                    # Deposit amounts: $5-$100, weighted towards lower amounts
                    deposit_amount = round(random.choices(
                        [5, 10, 15, 20, 25, 30, 50, 75, 100],
                        weights=[30, 25, 15, 10, 8, 5, 4, 2, 1],
                        k=1
                    )[0] + random.uniform(0, 0.99), 2)
                    
                    # Find applicable bonus package
                    applicable_package = None
                    bonus_amount = 0.00
                    for pkg in sorted(self.deposit_bonus_packages, key=lambda x: x['amount_cap'], reverse=True):
                        if deposit_amount >= pkg['amount_cap']:
                            applicable_package = pkg
                            bonus_amount = round(deposit_amount * pkg['bonus_percentage'], 2)
                            break
                    
                    total_credited = deposit_amount + bonus_amount
                    method = random.choice(payment_methods)
                    reference = f"DEP-{random.randint(100000, 999999)}"
                    # Test accounts always have completed deposits, regular students 95% completed
                    status = 'completed' if is_test_account else ('completed' if random.random() < 0.95 else 'pending')
                    
                    # Transaction date: within last 6 months
                    transaction_date = random_date_in_range(180, 0)
                    
                    # Store deposit data
                    deposit_data = {
                        'deposit_id': deposit_id,
                        'student_id': student['student_id'],
                        'deposit_amount': deposit_amount,
                        'bonus_amount': bonus_amount,
                        'total_credited': total_credited,
                        'payment_status': status
            }
                    self.deposits.append(deposit_data)
                    
                    # Update balance tracking for payment generation (only completed deposits)
                    if status == 'completed':
                        student_id = student['student_id']
                        if student_id not in student_balance_map:
                            student_balance_map[student_id] = 0.0
                        student_balance_map[student_id] += total_credited
                    
                    bulk_deposits.add_row([
                        deposit_id,
                        student['student_id'],
                        deposit_amount,
                        bonus_amount,
                        total_credited,
                        applicable_package['package_id'] if applicable_package else None,
                        method,
                        reference,
                        status,
                        transaction_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_deposits.get_statements():
            self.add_sql(stmt)
        
        # Add semester bonuses to balance map for payment generation logic
        for ssb in self.student_semester_bonuses:
            if ssb.get('received'):
                semester_bonus = next((sb for sb in self.semester_bonuses if sb['bonus_id'] == ssb['semester_bonus_id']), None)
                if semester_bonus:
                    student_id = ssb['student_id']
                    if student_id not in student_balance_map:
                        student_balance_map[student_id] = 0.0
                    student_balance_map[student_id] += semester_bonus['bonus_amount']
        
        # Store balance map for use in payment generation
        self.student_balance_map = student_balance_map
        
        # Note: Balances are computed dynamically via student_balance_view, no UPDATE statements needed
    
    
    def generate_fund_and_supplier_purchases(self):
        """Generate fund sources and supplier paper purchases."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- FUND SOURCES AND SUPPLIER PAPER PURCHASES DATA")
        self.add_sql("-- ============================================")
        
        # Generate fund sources
        bulk_funds = BulkInsertHelper("fund_source", [
            "fund_id", "fund_source_type", "fund_source_name", "amount",
            "received_date", "description", "created_at", "created_by"
        ])
        
        fund_types = ['school_budget', 'donation', 'revenue', 'other']
        fund_type_weights = [0.5, 0.2, 0.2, 0.1]  # 50% school budget, 20% donation, 20% revenue, 10% other
        
        # Generate 10-20 fund sources
        num_funds = random.randint(10, 20)
        creator_staff = random.choice(self.staff) if self.staff else None
        
        fund_source_names = {
            'school_budget': [
                'Annual Printing Budget 2023',
                'Annual Printing Budget 2024',
                'Semester 1 Printing Allocation',
                'Semester 2 Printing Allocation',
                'Emergency Printing Fund'
            ],
            'donation': [
                'Alumni Donation 2023',
                'Corporate Sponsorship - ABC Corp',
                'Community Donation',
                'Graduate Association Fund',
                'Anonymous Donation'
            ],
            'revenue': [
                'Student Purchase Revenue',
                'Printing Service Revenue Q1',
                'Printing Service Revenue Q2',
                'Additional Service Fees'
            ],
            'other': [
                'Miscellaneous Income',
                'Refund Recovery',
                'Other Sources'
            ]
        }
        
        for i in range(num_funds):
            fund_id = generate_uuid()
            fund_type = random.choices(fund_types, weights=fund_type_weights, k=1)[0]
            fund_name = random.choice(fund_source_names.get(fund_type, ['Fund Source']))
            
            # Generate realistic amounts based on type
            if fund_type == 'school_budget':
                amount = round(random.uniform(50000, 200000), 2)  # $50k - $200k
            elif fund_type == 'donation':
                amount = round(random.uniform(5000, 50000), 2)  # $5k - $50k
            elif fund_type == 'revenue':
                amount = round(random.uniform(10000, 80000), 2)  # $10k - $80k
            else:
                amount = round(random.uniform(1000, 20000), 2)  # $1k - $20k
            
            received_date = random_date_in_range(730, 0)  # Last 2 years
            description = f"Fund received from {fund_type.replace('_', ' ')}"
            created_at = received_date
            
            fund_data = {
                'fund_id': fund_id,
                'fund_source_type': fund_type,
                'fund_source_name': fund_name,
                'amount': amount,
                'received_date': received_date
            }
            self.fund_sources.append(fund_data)
            
            bulk_funds.add_row([
                fund_id, fund_type, fund_name, amount,
                received_date.strftime('%Y-%m-%d'), description,
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                creator_staff['staff_id'] if creator_staff else None
            ])
        
        for stmt in bulk_funds.get_statements():
            self.add_sql(stmt)
        
        # Generate supplier paper purchases
        bulk_purchases = BulkInsertHelper("supplier_paper_purchase", [
            "purchase_id", "supplier_name", "supplier_contact", "purchase_date",
            "total_amount_paid", "payment_method", "payment_reference", "payment_status",
            "invoice_number", "notes", "created_at", "created_by"
        ])
        
        supplier_names = [
            'Office Supplies Co.',
            'Paper Distributors Ltd.',
            'Printing Materials Inc.',
            'Stationery Solutions',
            'Campus Supply Chain',
            'Academic Materials Corp.',
            'Educational Supplies Co.'
        ]
        
        payment_methods = ['bank_transfer', 'check', 'cash', 'credit_card', 'wire_transfer']
        payment_statuses = ['completed', 'completed', 'completed', 'pending', 'completed']  # Mostly completed
        
        # Generate 15-30 supplier purchases
        num_purchases = random.randint(15, 30)
        
        for i in range(num_purchases):
            purchase_id = generate_uuid()
            supplier_name = random.choice(supplier_names)
            supplier_contact = f"{random.choice(['+84', ''])}{random.randint(900000000, 999999999)}"
            purchase_date = random_date_in_range(365, 0)  # Last year
            
            payment_method = random.choice(payment_methods)
            payment_reference = f"PAY{random.randint(100000, 999999)}"
            payment_status = random.choice(payment_statuses)
            invoice_number = f"INV-{random.randint(2023000, 2024999)}"
            notes = f"Paper purchase from {supplier_name}"
            created_at = purchase_date
            created_by = creator_staff['staff_id'] if creator_staff else None
            
            # Estimate total based on typical purchase (will be refined when items are added)
            # Typical purchase: 1-3 paper sizes, 5k-20k sheets, $0.03-$0.15 per sheet
            estimated_items = random.randint(1, 3)
            estimated_sheets = random.randint(5000, 20000)
            estimated_unit_price = random.uniform(0.03, 0.15)
            base_total = round(estimated_items * estimated_sheets * estimated_unit_price, 2)
            
            purchase_data = {
                'purchase_id': purchase_id,
                'supplier_name': supplier_name,
                'purchase_date': purchase_date,
                'total_amount_paid': base_total  # Estimated, actual breakdown in items
            }
            self.supplier_purchases.append(purchase_data)
            
            bulk_purchases.add_row([
                purchase_id, supplier_name, supplier_contact, purchase_date.strftime('%Y-%m-%d'),
                base_total, payment_method, payment_reference, payment_status,
                invoice_number, notes, created_at.strftime('%Y-%m-%d %H:%M:%S'), created_by
            ])
        
        for stmt in bulk_purchases.get_statements():
            self.add_sql(stmt)
        
        # Generate paper purchase items
        bulk_items = BulkInsertHelper("paper_purchase_item", [
            "purchase_item_id", "purchase_id", "page_size_id", "quantity",
            "unit_price", "total_price", "received_quantity", "received_date", "notes"
        ])
        
        # Unit prices per sheet (in USD) - A3 is more expensive, A5 is cheaper
        base_unit_prices = {
            'A3': 0.15,   # $0.15 per A3 sheet
            'A4': 0.05,   # $0.05 per A4 sheet
            'A5': 0.03    # $0.03 per A5 sheet
        }
        
        # Ensure page_sizes are available
        if not hasattr(self, 'page_sizes') or not self.page_sizes:
            raise ValueError("Page sizes not generated yet. Ensure generate_page_allocation_system() runs before generate_fund_and_supplier_purchases().")
        
        # For each purchase, add 1-3 different paper sizes
        for purchase in self.supplier_purchases:
            num_items = random.randint(1, 3)
            selected_sizes = random.sample(self.page_sizes, min(num_items, len(self.page_sizes)))
            
            for page_size in selected_sizes:
                item_id = generate_uuid()
                size_name = page_size['size_name']
                
                # Generate quantity based on size (A3: less quantity, A4: medium, A5: more)
                if size_name == 'A3':
                    quantity = random.randint(1000, 5000)  # 1k - 5k sheets
                elif size_name == 'A4':
                    quantity = random.randint(5000, 20000)  # 5k - 20k sheets
                else:  # A5
                    quantity = random.randint(3000, 10000)  # 3k - 10k sheets
                
                # Get base unit price and add some variance
                base_price = base_unit_prices.get(size_name, 0.05)
                unit_price = round(base_price * random.uniform(0.9, 1.1), 4)  # ±10% variance
                total_price = round(quantity * unit_price, 2)
                
                # Most items are fully received, some partially
                if random.random() < 0.9:  # 90% fully received
                    received_quantity = quantity
                    received_date = purchase['purchase_date'] + timedelta(days=random.randint(1, 14))
                else:  # 10% partially received or pending
                    received_quantity = random.randint(int(quantity * 0.5), quantity) if random.random() < 0.5 else None
                    received_date = purchase['purchase_date'] + timedelta(days=random.randint(1, 30)) if received_quantity else None
                
                notes = f"{quantity} sheets of {size_name} paper"
                
                item_data = {
                    'purchase_item_id': item_id,
                    'purchase_id': purchase['purchase_id'],
                    'page_size_id': page_size['page_size_id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                }
                self.paper_purchase_items.append(item_data)
                
                bulk_items.add_row([
                    item_id, purchase['purchase_id'], page_size['page_size_id'], quantity,
                    unit_price, total_price,
                    received_quantity, received_date.strftime('%Y-%m-%d') if received_date else None,
                    notes
                ])
        
        for stmt in bulk_items.get_statements():
            self.add_sql(stmt)
    
    def generate_system_configuration(self):
        """Generate system configuration and permitted file types."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- SYSTEM CONFIGURATION DATA")
        self.add_sql("-- ============================================")
        
        # System configurations
        bulk_config = BulkInsertHelper("system_configuration", [
            "config_id", "config_key", "config_value", "description", 
            "updated_at", "updated_by"
        ])
        
        configs = self.spec['system_configs']
        updater_staff = random.choice(self.staff) if self.staff else None
        updated_at = random_date_in_range(30, 0)
        
        for key, value in configs.items():
            config_id = generate_uuid()
            description = f"System configuration for {key.replace('_', ' ')}"
            
            bulk_config.add_row([
                config_id, key, str(value), description,
                updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                updater_staff['staff_id'] if updater_staff else None
            ])
        
        for stmt in bulk_config.get_statements():
            self.add_sql(stmt)
        
        # Permitted file types
        bulk_filetypes = BulkInsertHelper("permitted_file_type", [
            "file_type_id", "file_extension", "mime_type", "description",
            "is_permitted", "created_at", "updated_at", "updated_by"
        ])
        
        file_types = self.spec['permitted_extensions']
        
        for file_type in file_types:
            file_type_id = generate_uuid()
            created_at = random_date_in_range(365, 30)
            
            bulk_filetypes.add_row([
                file_type_id, file_type['extension'], file_type['mime_type'],
                file_type['description'], True,
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                created_at.strftime('%Y-%m-%d %H:%M:%S'),
                updater_staff['staff_id'] if updater_staff else None
            ])
        
        for stmt in bulk_filetypes.get_statements():
            self.add_sql(stmt)
    
    def generate_print_jobs(self):
        """Generate realistic print jobs with pages.

        Hard-coded test accounts: exactly 20 jobs each.
        Other students: random number of jobs based on spec distribution.
        """
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PRINT JOBS DATA")
        self.add_sql("-- ============================================")
        
        # Ensure page sizes are available
        if not hasattr(self, 'page_sizes') or not self.page_sizes:
            raise ValueError("Page sizes not generated yet. Ensure generate_page_allocation_system() runs before generate_print_jobs().")
        
        print(f"Available page sizes: {[ps['size_name'] for ps in self.page_sizes]}")
        
        avg_jobs = self.spec['avg_print_jobs_per_student']
        variance = self.spec['print_job_variance']
        
        # Distributions
        file_type_dist = self.spec['file_types']
        paper_size_dist = self.spec['paper_size_distribution']
        orientation_dist = self.spec['orientation_distribution']
        print_side_dist = self.spec['print_side_distribution']
        color_mode_dist = self.spec['color_mode_distribution']
        status_dist = self.spec['print_status_distribution']
        copy_dist = self.spec['copy_distribution']
        
        # Activity patterns
        hour_patterns = {
            'peak': self.spec['peak_hours'],
            'normal': self.spec['normal_hours'],
            'low': self.spec['low_hours'],
        }
        
        # Document templates
        doc_templates = self.spec['document_name_templates']
        courses = self.spec['course_names']
        
        # Enabled printers only
        enabled_printers = [p for p in self.printers if p['is_enabled']]
        
        # Use actual media files if available
        use_real_files = len(self.media_files) > 0
        
        # Uploaded files (saved documents)
        bulk_uploaded_files = BulkInsertHelper("uploaded_file", [
            "uploaded_file_id", "student_id", "file_name", "file_type", "file_size_kb", "file_url", "created_at"
        ])
        
        bulk_jobs = BulkInsertHelper("print_job", [
            "job_id", "student_id", "printer_id", "uploaded_file_id",
            "page_size_price_id", "color_mode_price_id",
            "page_discount_package_id", "page_orientation", "print_side",
            "number_of_copy", "total_pages", "subtotal_before_discount",
            "discount_percentage", "discount_amount", "total_price",
            "print_status", "start_time", "end_time", "created_at"
        ])
        
        bulk_pages = BulkInsertHelper("print_job_page", [
            "page_record_id", "job_id", "page_number"
        ])
        
        # Identify hard-coded test students
        test_student_emails = [
            "student.test@edu.vn",
            "phandienmanhthienk16@siu.edu.vn",
            "leanhtuank16@siu.edu.vn",
            "nguyenhongbaongock16@siu.edu.vn",
            "phanthanhthaituank16@siu.edu.vn",
            "lengocdangkhoak16@siu.edu.vn",
            "lyhieuvyk17@siu.edu.vn",
        ]
        test_student_ids = set()
        for email in test_student_emails:
            user = next((u for u in self.users if u['email'] == email), None)
            if user:
                student = next((s for s in self.students if s['user_id'] == user['user_id']), None)
                if student:
                    test_student_ids.add(student['student_id'])
        
        # Generate jobs
        for student in self.students:
            is_test_account = student['student_id'] in test_student_ids
            # Exactly 20 jobs for test accounts, otherwise use distribution
            if is_test_account:
                num_jobs = 20
            else:
                num_jobs = max(0, int(random.gauss(avg_jobs, variance)))
            
            for _ in range(num_jobs):
                job_id = generate_uuid()
                
                # Pick printer
                printer = random.choice(enabled_printers)
                
                # File info (uploaded_file)
                file_name = None
                file_url = None
                file_size_kb = None
                file_ext = None
                
                if use_real_files and self.media_files:
                    file_name = random.choice(self.media_files)
                    file_url = f"{SUPABASE_BASE_URL}/{SUPABASE_BUCKET_PRINT_JOBS}/{file_name}"
                    file_ext = os.path.splitext(file_name)[1].lstrip('.').lower() or weighted_choice(file_type_dist)
                    try:
                        media_path = os.path.join(MEDIA_FOLDER, file_name)
                        if os.path.exists(media_path):
                            file_size_kb = max(1, os.path.getsize(media_path) // 1024)
                        else:
                            file_size_kb = random.randint(100, 10240)
                    except Exception:
                        file_size_kb = random.randint(100, 10240)
                else:
                    file_ext = weighted_choice(file_type_dist)
                    file_name = generate_document_name(doc_templates, courses, f".{file_ext}")
                    file_url = f"{SUPABASE_BASE_URL}/{SUPABASE_BUCKET_PRINT_JOBS}/{file_name}"
                    if file_ext == 'pdf':
                        file_size_kb = random.randint(500, 5000)
                    elif file_ext in ['jpg', 'png', 'webp']:
                        file_size_kb = random.randint(200, 2000)
                    elif file_ext == 'docx':
                        file_size_kb = random.randint(100, 1000)
                    elif file_ext in ['xlsx', 'xls']:
                        file_size_kb = random.randint(50, 500)
                    elif file_ext == 'pptx':
                        file_size_kb = random.randint(1000, 10000)
                    else:
                        file_size_kb = random.randint(100, 1000)
                
                # Create uploaded_file record
                uploaded_file_id = generate_uuid()
                # Use "now" for uploaded file created_at; job created_at is set separately below
                uploaded_created_at = datetime.now()
                bulk_uploaded_files.add_row([
                    uploaded_file_id,
                    student['student_id'],
                    file_name,
                    file_ext,
                    file_size_kb,
                    file_url,
                    uploaded_created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
                # Paper size
                paper_size_name = weighted_choice(paper_size_dist)
                matching_page_size = next(
                    (ps for ps in self.page_sizes if ps["size_name"] == paper_size_name),
                    None
                )
                if not matching_page_size:
                    matching_page_size = next(
                        (ps for ps in self.page_sizes if ps["size_name"] == "A4"),
                        self.page_sizes[0] if self.page_sizes else None
                    )
                if not matching_page_size:
                    raise ValueError(f"No page sizes available. Available sizes: {[ps['size_name'] for ps in self.page_sizes]}")
                
                paper_size_id = matching_page_size["page_size_id"]
                matching_page_size_price = next(
                    (psp for psp in self.page_size_prices if psp['page_size_id'] == paper_size_id),
                    None
                )
                if not matching_page_size_price:
                    raise ValueError(f"No page_size_price found for page_size_id: {paper_size_id}")
                page_size_price_id = matching_page_size_price['price_id']
                
                # Other settings
                orientation = weighted_choice(orientation_dist)
                print_side = weighted_choice(print_side_dist)
                color_mode_name = weighted_choice(color_mode_dist)
                num_copies = int(weighted_choice(copy_dist))
                status = weighted_choice(status_dist)
                
                # Color mode price
                matching_color_mode_price = next(
                    (cmp for cmp in self.color_mode_prices if cmp['color_mode_name'] == color_mode_name),
                    None
                )
                if not matching_color_mode_price:
                    raise ValueError(f"No color_mode_price found for color_mode: {color_mode_name}")
                color_mode_price_id = matching_color_mode_price['setting_id']
                
                # Timing
                created_at = random_datetime_with_pattern(365, hour_patterns)
                start_time = None
                end_time = None
                if status in ['completed', 'failed']:
                    start_time = created_at + timedelta(minutes=random.randint(1, 30))
                    duration_minutes = random.randint(1, 15)
                    end_time = start_time + timedelta(minutes=duration_minutes)
                elif status == 'printing':
                    start_time = created_at + timedelta(minutes=random.randint(1, 30))
                
                # Pages
                avg_pages = self.spec['avg_pages_per_document']
                page_variance = self.spec['pages_variance']
                min_pages = self.spec['min_pages_per_job']
                max_pages = self.spec['max_pages_per_job']
                num_pages = max(min_pages, min(max_pages, int(random.gauss(avg_pages, page_variance))))
                total_pages = num_pages * num_copies
                
                # Pricing
                color_mode_price_per_page = matching_color_mode_price['price_per_page']
                subtotal_before_discount = total_pages * color_mode_price_per_page
                
                page_discount_package_id = None
                discount_percentage = None
                for pdp in sorted(self.page_discount_packages, key=lambda x: x.get('min_pages', 0), reverse=True):
                    if total_pages >= pdp['min_pages']:
                        page_discount_package_id = pdp['package_id']
                        discount_percentage = pdp['discount_percentage']
                        break
                
                discount_amount = subtotal_before_discount * (discount_percentage if discount_percentage else 0.0)
                total_price = subtotal_before_discount - discount_amount
                
                # Store job
                job_data = {
                    'job_id': job_id,
                    'student_id': student['student_id'],
                    'printer_id': printer['printer_id'],
                    'uploaded_file_id': uploaded_file_id,
                    'num_pages': num_pages,
                    'total_pages': total_pages,
                    'page_size_price_id': page_size_price_id,
                    'color_mode_price_id': color_mode_price_id,
                    'page_discount_package_id': page_discount_package_id,
                    'paper_size_name': matching_page_size['size_name'],
                    'num_copies': num_copies,
                    'subtotal_before_discount': subtotal_before_discount,
                    'discount_percentage': discount_percentage,
                    'discount_amount': discount_amount,
                    'total_price': total_price,
                    'status': status,
                    'created_at': created_at
                }
                self.print_jobs.append(job_data)
                
                # Add to bulk insert
                bulk_jobs.add_row([
                    job_id, student['student_id'], printer['printer_id'],
                    uploaded_file_id,
                    page_size_price_id, color_mode_price_id, page_discount_package_id,
                    orientation, print_side, num_copies,
                    total_pages,
                    round(subtotal_before_discount, 2),
                    discount_percentage if discount_percentage is not None else None,
                    round(discount_amount, 2),
                    round(total_price, 2),
                    status,
                    start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                    end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None,
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
                # Pages for this job
                for page_num in range(1, num_pages + 1):
                    page_record_id = generate_uuid()
                    bulk_pages.add_row([page_record_id, job_id, page_num])
        
        # Flush SQL
        for stmt in bulk_uploaded_files.get_statements():
            self.add_sql(stmt)
        for stmt in bulk_jobs.get_statements():
            self.add_sql(stmt)
        for stmt in bulk_pages.get_statements():
            self.add_sql(stmt)
        
        # Generate payments for completed print jobs
        self.generate_payments()
    
    def generate_payments(self):
        """Generate payment records for print jobs."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PAYMENT DATA (for Print Jobs)")
        self.add_sql("-- ============================================")
        
        bulk_payments = BulkInsertHelper("payment", [
            "payment_id", "job_id", "student_id", "amount_paid_directly", "amount_paid_from_balance",
            "total_amount", "payment_method", "payment_reference", "payment_status", "transaction_date"
        ])
        
        # Get payment methods - ensure it's a list
        payment_methods_raw = self.spec.get('payment_methods', ['credit_card', 'debit_card', 'bank_transfer', 'e_wallet'])
        if isinstance(payment_methods_raw, dict):
            payment_methods = list(payment_methods_raw.keys())
        elif isinstance(payment_methods_raw, list):
            payment_methods = payment_methods_raw
        else:
            payment_methods = ['credit_card', 'debit_card', 'bank_transfer', 'e_wallet']
        
        # Build lookup maps for pricing
        page_size_price_map = {}  # price_id -> price
        for psp in self.page_size_prices:
            if psp.get('is_active', True):
                page_size_price_map[psp['price_id']] = psp['page_price']
        
        color_mode_price_map = {}  # setting_id -> price_per_page
        for cmp in self.color_mode_prices:
            if cmp.get('is_active', True):
                color_mode_price_map[cmp['setting_id']] = cmp['price_per_page']
        
        page_discount_map = {}  # package_id -> discount_percentage
        for pdp in self.page_discount_packages:
            if pdp.get('is_active', True):
                page_discount_map[pdp['package_id']] = pdp['discount_percentage']
        
        # Use pre-calculated balance map from deposit generation
        # This includes deposits and semester bonuses, but not payments yet
        student_balance_map = getattr(self, 'student_balance_map', {}).copy()
        
        # Generate payments only for completed print jobs
        for job in self.print_jobs:
            # Only create payment for completed jobs
            job_record = next((j for j in self.print_jobs if j.get('job_id') == job.get('job_id')), None)
            if not job_record:
                continue
            
            # Check if this is a test account job
            student_id = job['student_id']
            is_test_account = False
            test_student_emails = [
                "student.test@edu.vn",
                "phandienmanhthienk16@siu.edu.vn",
                "leanhtuank16@siu.edu.vn",
                "nguyenhongbaongock16@siu.edu.vn",
                "phanthanhthaituank16@siu.edu.vn",
                "lengocdangkhoak16@siu.edu.vn",
                "lyhieuvyk17@siu.edu.vn",
            ]
            student = next((s for s in self.students if s['student_id'] == student_id), None)
            if student:
                user = next((u for u in self.users if u['user_id'] == student['user_id']), None)
                if user and user['email'] in test_student_emails:
                    is_test_account = True
            
            # Test account jobs always get payments, regular jobs 90% get payments
            if not is_test_account and random.random() > 0.9:
                continue  # Skip 10% of regular jobs (they might be failed/cancelled)
            
            payment_id = generate_uuid()
            
            # Use stored total_price from print_job (already calculated)
            total_amount = job.get('total_price', 0.0)
            
            # Determine payment split: use balance first, then direct payment
            student_balance = student_balance_map.get(student_id, 0.0)
            amount_paid_from_balance = min(total_amount, student_balance)
            amount_paid_directly = max(0, total_amount - amount_paid_from_balance)
            
            # Update balance tracking (deduct from balance)
            if student_id in student_balance_map:
                student_balance_map[student_id] = max(0, student_balance_map[student_id] - amount_paid_from_balance)
            
            # Payment method: if using balance, method is 'balance', otherwise random method
            if amount_paid_from_balance > 0 and amount_paid_directly == 0:
                method = 'balance'
            elif amount_paid_directly > 0:
                method = random.choice(payment_methods)
            else:
                method = random.choice(payment_methods)
            
            payment_reference = f"PAY-{random.randint(100000, 999999)}"
            # Test account payments always completed, regular payments 95% completed
            payment_status = 'completed' if is_test_account else ('completed' if random.random() < 0.95 else 'pending')
            
            # Transaction date should match or be slightly after job creation
            job_created_at = job.get('created_at')
            if isinstance(job_created_at, str):
                job_created_at = datetime.strptime(job_created_at, '%Y-%m-%d %H:%M:%S')
            elif isinstance(job_created_at, datetime):
                pass
            else:
                job_created_at = random_date_in_range(180, 0)
            
            # Payment happens at or slightly after job creation (0-2 hours later)
            transaction_date = job_created_at + timedelta(minutes=random.randint(0, 120))
            
            self.payments.append({
                'payment_id': payment_id,
                'job_id': job.get('job_id'),
                'student_id': student_id,
                'amount_paid_directly': amount_paid_directly,
                'amount_paid_from_balance': amount_paid_from_balance,
                'total_amount': total_amount
            })
            
            bulk_payments.add_row([
                payment_id,
                job.get('job_id'),
                student_id,
                amount_paid_directly,
                amount_paid_from_balance,
                total_amount,
                method,
                payment_reference,
                payment_status,
                transaction_date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk_payments.get_statements():
            self.add_sql(stmt)
        
        # Note: Balances are computed dynamically via student_balance_view, no UPDATE statements needed
    
    def generate_activity_logs(self):
        """Generate printer logs for the printer_log table."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PRINTER LOGS DATA")
        self.add_sql("-- ============================================")
        
        bulk = BulkInsertHelper("printer_log", [
            "log_id", "printer_id", "log_type", "severity", "description",
            "job_id", "user_id", "details", "error_code", "is_resolved",
            "resolved_at", "resolved_by", "resolution_notes", "ip_address", "created_at"
        ])
        
        log_types = ['print_job', 'error', 'maintenance', 'status_change', 'configuration', 'admin_action']
        severities = ['info', 'warning', 'error', 'critical']
        
        # Generate logs for each printer
        for printer in self.printers:
            # Each printer has 5-15 logs
            num_logs = random.randint(5, 15)
            
            # Look up room, floor, and building information
            room = next((r for r in self.rooms if r['room_id'] == printer['room_id']), None)
            floor = None
            building = None
            if room:
                floor = next((f for f in self.floors if f['floor_id'] == room['floor_id']), None)
                if floor:
                    building = next((b for b in self.buildings if b['building_id'] == floor['building_id']), None)
            
            building_name = building['building_name'] if building else 'Unknown Building'
            room_code = room['room_code'] if room else 'Unknown Room'
            
            # Get print jobs for this printer
            printer_jobs = [job for job in self.print_jobs if job.get('printer_id') == printer['printer_id']]
            
            for _ in range(num_logs):
                log_id = generate_uuid()
                log_type = random.choice(log_types)
                
                # Determine severity based on log type
                if log_type == 'error':
                    severity = random.choice(['error', 'critical'])
                elif log_type == 'maintenance':
                    severity = random.choice(['info', 'warning'])
                elif log_type == 'print_job':
                    severity = 'info'
                else:
                    severity = random.choice(severities)
                
                # Generate description based on log type
                job_id = None
                user_id = None
                error_code = None
                details = None
                description = ""
                
                if log_type == 'print_job':
                    # Link to an actual print job if available
                    if printer_jobs and random.random() < 0.7:  # 70% chance to link to real job
                        job = random.choice(printer_jobs)
                        job_id = job['job_id']
                        # Get student for this job
                        student = next((s for s in self.students if s['student_id'] == job['student_id']), None)
                        if student:
                            user_id = student['user_id']
                        num_pages = job.get('num_pages', 1)
                        description = f"Print job submitted: {num_pages} page(s)"
                    else:
                        description = "Print job queued successfully"
                    severity = 'info'
                
                elif log_type == 'error':
                    error_types = [
                        ('PAPER_JAM', 'Paper jam detected in paper path'),
                        ('OUT_OF_TONER', 'Toner cartridge is empty'),
                        ('LOW_TONER', 'Toner level is low'),
                        ('OUT_OF_PAPER', 'Paper tray is empty'),
                        ('DOOR_OPEN', 'Printer door is open'),
                        ('NETWORK_ERROR', 'Network connection lost'),
                        ('OFFLINE', 'Printer went offline'),
                        ('HARDWARE_ERROR', 'Hardware malfunction detected')
                    ]
                    error_code, error_desc = random.choice(error_types)
                    description = error_desc
                    details = f'{{"error_type": "{error_code}", "location": "{building_name} Room {room_code}"}}'
                
                elif log_type == 'maintenance':
                    maintenance_actions = [
                        "Scheduled maintenance performed",
                        "Toner cartridge replaced",
                        "Paper tray refilled",
                        "Cleaning cycle completed",
                        "Firmware update installed",
                        "Calibration completed"
                    ]
                    description = random.choice(maintenance_actions)
                    # Maintenance logs are usually performed by staff
                    staff_member = random.choice(self.staff) if self.staff else None
                    if staff_member:
                        user_id = staff_member['user_id']
                    details = f'{{"maintenance_type": "routine", "location": "{building_name} Room {room_code}"}}'
                
                elif log_type == 'status_change':
                    status_changes = [
                        "Printer status changed to idle",
                        "Printer enabled for student use",
                        "Printer disabled for maintenance",
                        "Printer status changed to printing",
                        "Printer status changed to maintained"
                    ]
                    description = random.choice(status_changes)
                    # Status changes can be by staff or system
                    if random.random() < 0.6:  # 60% by staff
                        staff_member = random.choice(self.staff) if self.staff else None
                        if staff_member:
                            user_id = staff_member['user_id']
                
                elif log_type == 'configuration':
                    config_changes = [
                        "Printer network settings updated",
                        "Default paper size changed",
                        "Print quality settings adjusted",
                        "Printer name updated",
                        "Access permissions modified"
                    ]
                    description = random.choice(config_changes)
                    # Configuration changes are always by staff
                    staff_member = random.choice(self.staff) if self.staff else None
                    if staff_member:
                        user_id = staff_member['user_id']
                
                elif log_type == 'admin_action':
                    admin_actions = [
                        "Printer added to system",
                        "Printer removed from system",
                        "Printer location updated",
                        "Printer model information updated",
                        "Printer access logs reviewed"
                    ]
                    description = random.choice(admin_actions)
                    # Admin actions are always by staff
                    staff_member = random.choice(self.staff) if self.staff else None
                    if staff_member:
                        user_id = staff_member['user_id']
                
                # Generate resolution info for errors
                is_resolved = 0
                resolved_at = None
                resolved_by = None
                resolution_notes = None
                
                if log_type == 'error' and random.random() < 0.6:  # 60% of errors are resolved
                    is_resolved = 1
                    created_at = random_date_in_range(365, 7)
                    resolved_at = created_at + timedelta(hours=random.randint(1, 48))
                    staff_member = random.choice(self.staff) if self.staff else None
                    if staff_member:
                        resolved_by = staff_member['user_id']
                    resolution_notes = random.choice([
                        "Issue resolved by clearing paper jam",
                        "Toner cartridge replaced",
                        "Paper tray refilled",
                        "Network connection restored",
                        "Hardware reset performed",
                        "Issue resolved after maintenance"
                    ])
                else:
                    created_at = random_date_in_range(365, 0)
                
                # Generate IP address (some logs have it, some don't)
                ip_address = None
                if log_type in ['print_job', 'admin_action', 'configuration'] and random.random() < 0.7:
                    ip_address = f"{random.randint(192, 255)}.{random.randint(168, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
                
                bulk.add_row([
                    log_id, printer['printer_id'], log_type, severity, description,
                    job_id, user_id, details, error_code, is_resolved,
                    resolved_at.strftime('%Y-%m-%d %H:%M:%S') if resolved_at else None,
                    resolved_by, resolution_notes, ip_address,
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk.get_statements():
            self.add_sql(stmt)
    
    def generate_audit_logs(self):
        """Generate system audit logs."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- SYSTEM AUDIT LOGS DATA")
        self.add_sql("-- ============================================")
        
        bulk = BulkInsertHelper("system_audit_log", [
            "audit_id", "user_id", "action_type", "table_name", "record_id",
            "previous_audit_id", "changed_field", "ip_address", "user_agent",
            "action_timestamp"
        ])
        
        tables = ['user', 'student', 'staff', 'print_job', 'system_configuration']
        actions = ['INSERT', 'UPDATE', 'DELETE', 'SELECT']
        
        # Sample user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        # Generate sample audit logs (limited number for performance)
        num_audit_logs = 1000
        
        for _ in range(num_audit_logs):
            audit_id = generate_uuid()
            user = random.choice(self.users)
            action = random.choice(actions)
            table = random.choice(tables)
            record_id = generate_uuid()
            
            # Generate fake IP address
            ip = f"{random.randint(192, 255)}.{random.randint(168, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            user_agent = random.choice(user_agents)
            timestamp = random_date_in_range(365, 0)
            
            # Simple changed field JSON
            changed_field = '{"status": "updated"}' if action == 'UPDATE' else None
            
            bulk.add_row([
                audit_id, user['user_id'], action, table, record_id,
                None, changed_field, ip, user_agent,
                timestamp.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk.get_statements():
            self.add_sql(stmt)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("=" * 70)
    print("SMART PRINTING SERVICE SYSTEM (SSPS)")
    print("BULK INSERT DATA GENERATOR")
    print("=" * 70)
    print()
    
    # Load specification
    print(f"Loading specification from: {SPEC_FILE_PATH}")
    try:
        spec = load_spec(SPEC_FILE_PATH)
    except Exception as e:
        print(f"Error loading spec file: {e}")
        return
    
    # Load media files
    print(f"\nScanning media folder: {MEDIA_FOLDER}")
    media_files = get_media_files(MEDIA_FOLDER)
    print(f"  Media files found: {len(media_files)}")
    
    # Load profile picture files
    print(f"\nScanning profile pictures folder: {PROFILE_PICS_FOLDER}")
    profile_pics_files = get_media_files(PROFILE_PICS_FOLDER)
    print(f"  Profile picture files found: {len(profile_pics_files)}")
    
    # Generate data
    print("\n" + "=" * 70)
    print("GENERATING DATA (BULK INSERTS)")
    print("=" * 70)
    print()
    
    generator = PrintingServiceDataGenerator(spec, media_files, profile_pics_files)
    
    try:
        sql_content = generator.generate_all_data()
        
        # Prepare final output
        final_output = []
        
        if INCLUDE_SCHEMA_RESET:
            # Include delete and design scripts
            try:
                # Use utf-8-sig to strip any BOM from schema files
                with open(delete_path, 'r', encoding='utf-8-sig') as f:
                    delete_content = f.read()
                
                # Remove USE statements and GO statements after USE if SKIP_USE_STATEMENT is True
                if SKIP_USE_STATEMENT:
                    lines = delete_content.split('\n')
                    filtered_lines = []
                    skip_next_go = False
                    for i, line in enumerate(lines):
                        # Skip USE statements
                        if line.strip().upper().startswith('USE '):
                            skip_next_go = True
                            continue
                        # Skip GO after USE statement
                        if skip_next_go and line.strip().upper() == 'GO':
                            skip_next_go = False
                            continue
                        skip_next_go = False
                        filtered_lines.append(line)
                    delete_content = '\n'.join(filtered_lines)
                
                final_output.append("-- ============================================")
                final_output.append("-- CLEANUP EXISTING DATA")
                final_output.append("-- ============================================")
                final_output.append(delete_content)
                final_output.append("")
                
                with open(design_path, 'r', encoding='utf-8-sig') as f:
                    design_content = f.read()
                
                # Remove USE statements and GO statements after USE if SKIP_USE_STATEMENT is True
                if SKIP_USE_STATEMENT:
                    lines = design_content.split('\n')
                    filtered_lines = []
                    skip_next_go = False
                    for i, line in enumerate(lines):
                        # Skip USE statements
                        if line.strip().upper().startswith('USE '):
                            skip_next_go = True
                            continue
                        # Skip GO after USE statement
                        if skip_next_go and line.strip().upper() == 'GO':
                            skip_next_go = False
                            continue
                        skip_next_go = False
                        filtered_lines.append(line)
                    design_content = '\n'.join(filtered_lines)
                    
                final_output.append("-- ============================================")
                final_output.append("-- CREATE DATABASE SCHEMA")
                final_output.append("-- ============================================")
                final_output.append(design_content)
                final_output.append("")
            except Exception as e:
                print(f"Warning: Could not include schema files: {e}")
        
        if not SKIP_USE_STATEMENT:
            final_output.append("USE printing_service_db;")
            final_output.append("GO")
            final_output.append("")
        
        final_output.append("-- ============================================")
        final_output.append("-- INSERT TEST DATA")
        final_output.append("-- ============================================")
        final_output.append(sql_content)
        
        # Write to output file
        os.makedirs(os.path.dirname(OUTPUT_SQL_FILE), exist_ok=True)
        with open(OUTPUT_SQL_FILE, 'w', encoding='utf-8') as f:
            f.write("\n".join(final_output))
        
        print("\n" + "=" * 70)
        print("GENERATION COMPLETE")
        print("=" * 70)
        print(f"Total SQL statements: {len(generator.sql_statements)}")
        print(f"Users generated: {len(generator.users)}")
        print(f"Faculties generated: {len(generator.faculties)}")
        print(f"Departments generated: {len(generator.departments)}")
        print(f"Majors generated: {len(generator.majors)}")
        print(f"Academic years generated: {len(generator.academic_years)}")
        print(f"Semesters generated: {len(generator.semesters)}")
        print(f"Classes generated: {len(generator.classes)}")
        print(f"Students generated: {len(generator.students)}")
        print(f"Staff generated: {len(generator.staff)}")
        print(f"Fund sources generated: {len(generator.fund_sources)}")
        print(f"Supplier purchases generated: {len(generator.supplier_purchases)}")
        print(f"Paper purchase items generated: {len(generator.paper_purchase_items)}")
        print(f"Printers generated: {len(generator.printers)}")
        print(f"Print jobs generated: {len(generator.print_jobs)}")
        print(f"Output file: {OUTPUT_SQL_FILE}")
        print()
        print("Ready to import into database!")
        print()
        print("Generating PNG files in batch (faster)...")
        # Generate PNGs in batch using optimized converter
        try:
            import sys
            script_dir = os.path.dirname(os.path.abspath(__file__))
            maps_dir = os.path.join(script_dir, "..", "maps")
            maps_dir_abs = os.path.abspath(maps_dir)
            if maps_dir_abs not in sys.path:
                sys.path.insert(0, maps_dir_abs)
            from convert_svgs_to_png import convert_all_svgs_fast
            
            # Convert both directories
            floors_diagrams_dir = os.path.join(maps_dir, "floors_diagrams")
            output_test_dir = os.path.join(maps_dir, "output_test")
            
            for dir_path in [floors_diagrams_dir, output_test_dir]:
                if os.path.exists(dir_path):
                    convert_all_svgs_fast(dir_path)
            print("PNG generation complete!")
        except Exception as e:
            print(f"Warning: Could not generate PNGs in batch: {e}")
            print("  You can run: cd maps && python convert_svgs_to_png.py")
        
    except Exception as e:
        print(f"Error during data generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
