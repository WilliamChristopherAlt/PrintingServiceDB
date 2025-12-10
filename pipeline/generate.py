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
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ============================================================================
# CONFIGURATION - Update these paths as needed  
# ============================================================================
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE_PATH = os.path.join(script_dir, "specs.yaml")
MEDIA_FOLDER = os.path.join(script_dir, "..", "medias")
OUTPUT_SQL_FILE = os.path.join(script_dir, "..", "sql", "insert.sql")

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
    def __init__(self, spec, media_files):
        self.spec = spec
        self.media_files = media_files
        self.sql_statements = []
        
        # Data storage for relationships
        self.users = []
        self.students = []
        self.staff = []
        self.brands = []
        self.models = []
        self.buildings = []
        self.rooms = []
        self.printers = []
        self.print_jobs = []
        
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
        
        # Discount packs (initialized empty, populated in generate_discount_packs)
        self.discount_packs = []
        
        # System state
        self.current_academic_year = spec['current_academic_year']
        self.semester_names = spec['semester_names']
        
    def add_sql(self, statement):
        """Add a SQL statement."""
        self.sql_statements.append(statement)
    
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
        
        print("Generating discount packages...")
        self.generate_discount_packs()
        
        print("Generating printer infrastructure...")
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
        staff_test_password_hash = generate_password_hash("SmartPrint@123!")
        
        bulk = BulkInsertHelper("user", [
            "user_id", "email", "full_name", "password_hash",
            "user_type", "phone_number", "created_at", "is_active"
        ])
        
        phone_prefixes = self.spec['phone_prefixes']
        
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
                'student', test_phone, test_created_at.strftime('%Y-%m-%d %H:%M:%S'), 1
            ])
        
        # Test staff account (password SmartPrint@123!)
        test_staff_id = generate_uuid()
        test_staff_email = "staff.test@edu.vn"
        if test_staff_email not in used_emails:
            used_emails.add(test_staff_email)
        test_staff_phone = generate_phone_number(phone_prefixes)
        test_staff_created_at = random_date_in_range(365, 30)
        
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
            'staff', test_staff_phone, test_staff_created_at.strftime('%Y-%m-%d %H:%M:%S'), 1
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
                user_type, phone, created_at.strftime('%Y-%m-%d %H:%M:%S'), is_active
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
            "enrollment_date", "status"
        ])
        
        student_users = [user for user in self.users if user['user_type'] == 'student' and user['is_active']]
        students_per_class = self.spec['students_per_class']
        
        student_index = 0
        
        # Find a suitable class for assignment (current/recent academic year)
        suitable_classes = [
            class_info for class_info in self.classes
            if any(ay['academic_year_id'] == class_info['academic_year_id'] and 
                  ay['year_name'] in ['2023-2024', '2024-2025'] 
                  for ay in self.academic_years)
        ]
        
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
                    enrollment_date.strftime('%Y-%m-%d'), 'active'
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
        """Generate printer brands, models, and physical printers."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PRINTER INFRASTRUCTURE DATA")
        self.add_sql("-- ============================================")
        
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
            "supports_color", "supports_duplex", "pages_per_second", "created_at"
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
                
                model_data = {
                    'model_id': model_id,
                    'brand_id': brand['brand_id'],
                    'name': model_config['name'],
                    'max_paper_size_id': max_paper_size_id,
                    'supports_color': model_config['supports_color'],
                    'supports_duplex': model_config['supports_duplex'],
                    'pages_per_second': pages_per_second
                }
                
                self.models.append(model_data)
                
                bulk_models.add_row([
                    model_id, brand['brand_id'], model_config['name'], description,
                    max_paper_size_id, model_config['supports_color'],
                    model_config['supports_duplex'], pages_per_second,
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_models.get_statements():
            self.add_sql(stmt)
        
        # Generate physical printers
        bulk_printers = BulkInsertHelper("printer_physical", [
            "printer_id", "model_id", "room_id", "serial_number", "is_enabled",
            "status", "printing_status", "installed_date", "last_maintenance_date",
            "created_at", "created_by"
        ])
        
        # First generate buildings
        bulk_buildings = BulkInsertHelper("building", [
            "building_id", "building_code", "address", "campus_name", "created_at"
        ])
        
        campuses = self.spec['campuses']
        
        for campus in campuses:
            for building_name in campus['buildings']:
                building_id = generate_uuid()
                building_code = building_name[:10].upper().replace(' ', '')
                address = f"{building_name}, {campus['name']} Campus"
                
                building_data = {
                    'building_id': building_id,
                    'building_code': building_code,
                    'building_name': building_name,
                    'campus_name': campus['name'],
                    'address': address
                }
                
                self.buildings.append(building_data)
                
                created_at = random_date_in_range(3650, 365)
                bulk_buildings.add_row([
                    building_id,
                    sql_escape(building_code),
                    sql_escape(address),
                    sql_escape(campus['name']),
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_buildings.get_statements():
            self.add_sql(stmt)
        
        # Generate rooms
        bulk_rooms = BulkInsertHelper("room", [
            "room_id", "building_id", "room_code", "room_type", "created_at"
        ])
        
        room_types = ['Classroom', 'Lab', 'Office', 'Library', 'Study Hall', 'Conference Room']
        printers_range = self.spec['printers_per_building']
        
        for building in self.buildings:
            num_rooms = random.randint(printers_range['min'], printers_range['max'])
            
            for room_num in range(1, num_rooms + 1):
                room_id = generate_uuid()
                room_code = f"{room_num:03d}"
                room_type = random.choice(room_types)
                
                room_data = {
                    'room_id': room_id,
                    'building_id': building['building_id'],
                    'building_code': building['building_code'],
                    'campus_name': building['campus_name'],
                    'room_code': room_code,
                    'room_type': room_type
                }
                
                self.rooms.append(room_data)
                
                created_at = random_date_in_range(2190, 180)
                bulk_rooms.add_row([
                    room_id,
                    building['building_id'],
                    sql_escape(room_code),
                    sql_escape(room_type),
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        for stmt in bulk_rooms.get_statements():
            self.add_sql(stmt)
        
        # Get a random staff member as creator
        creator_staff = random.choice(self.staff) if self.staff else None
        
        # Generate printers for rooms (about 70% of rooms have printers)
        status_options = ['idle', 'idle', 'idle', 'idle', 'idle', 'printing', 'maintained', 'unplugged']  # Weighted: mostly idle
        printing_status_options = ['printing', 'paper_jam', 'low_toner', 'out_of_paper', 'network_error', 'error']
        
        for room in self.rooms:
            if random.random() < 0.7:  # 70% chance of having a printer
                printer_id = generate_uuid()
                model = random.choice(self.models)
                
                serial_number = generate_serial_number()
                installed_date = random_date_in_range(1095, 30)
                last_maintenance = random_date_in_range(90, 0)
                created_at = installed_date
                is_enabled = random.choice([True, True, True, False])  # 75% enabled
                
                # Generate status
                if not is_enabled:
                    status = random.choice(['unplugged', 'maintained'])
                else:
                    status = random.choice(status_options)
                
                # Generate printing_status (only set when status is 'printing', otherwise NULL)
                printing_status = None
                if status == 'printing':
                    # 85% chance of normal printing, 15% chance of error
                    if random.random() < 0.85:
                        printing_status = 'printing'
                    else:
                        printing_status = random.choice(printing_status_options)
                
                printer_data = {
                    'printer_id': printer_id,
                    'model_id': model['model_id'],
                    'room_id': room['room_id'],
                    'campus_name': room['campus_name'],
                    'building_code': room['building_code'],
                    'room_code': room['room_code'],
                    'room_type': room['room_type'],
                    'is_enabled': is_enabled,
                    'status': status,
                    'printing_status': printing_status
                }
                
                self.printers.append(printer_data)
                self.printer_by_id[printer_id] = printer_data
                
                bulk_printers.add_row([
                    printer_id, model['model_id'], room['room_id'], serial_number, is_enabled,
                    status, printing_status,
                    installed_date.strftime('%Y-%m-%d'),
                    last_maintenance.strftime('%Y-%m-%d'),
                    created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    creator_staff['staff_id'] if creator_staff else None
                ])
        
        for stmt in bulk_printers.get_statements():
            self.add_sql(stmt)
    
    def generate_page_allocation_system(self):
        """Generate page sizes, allocations, and student page purchases."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PAGE ALLOCATION AND PURCHASE SYSTEM DATA")
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
        
        # Find A4 page size for default allocation
        a4_page_size = next(ps for ps in self.page_sizes if ps["size_name"] == "A4")
        
        # Generate page allocations
        bulk_allocations = BulkInsertHelper("page_allocation", [
            "allocation_id", "semester", "academic_year", "page_type_id", 
            "default_page_count", "allocation_date", "created_at", "created_by"
        ])
        
        semesters = self.spec['semester_names']
        default_pages = self.spec['default_pages_per_semester']
        current_year = self.current_academic_year
        creator_staff = random.choice(self.staff) if self.staff else None
        
        # Generate allocations for current year and previous year
        for year in [current_year - 1, current_year]:
            for semester in semesters:
                allocation_id = generate_uuid()
                allocation_date = datetime(year, 1 if semester == "HK1" else (5 if semester == "HK2" else 8), 1)
                
                bulk_allocations.add_row([
                    allocation_id, semester, year, a4_page_size["page_size_id"],
                    default_pages, allocation_date.strftime('%Y-%m-%d'),
                    allocation_date.strftime('%Y-%m-%d %H:%M:%S'),
                    creator_staff['staff_id'] if creator_staff else None
                ])
        
        for stmt in bulk_allocations.get_statements():
            self.add_sql(stmt)
        
        # Generate student page purchases
        bulk_purchases = BulkInsertHelper("student_page_purchase", [
            "purchase_id", "student_id", "page_size_id", "quantity", "amount_paid",
            "discount_pack_id", "payment_method", "payment_reference", "payment_status", "transaction_date"
        ])
        
        payment_methods = self.spec['payment_methods']
        page_price = self.spec['page_price_per_a4']
        purchase_rate = self.spec['page_purchase_rate']
        avg_additional = self.spec['avg_additional_pages']
        variance = self.spec['additional_pages_variance']
        success_rate = self.spec['payment_success_rate']
        
        # Price multipliers for different page sizes
        price_multipliers = {"A3": 2.0, "A4": 1.0, "A5": 0.5}
        
        for student in self.students:
            if random.random() < purchase_rate:
                # Generate 1-3 transactions per student
                num_transactions = random.randint(1, 3)
                
                for _ in range(num_transactions):
                    purchase_id = generate_uuid()
                    
                    # Choose page size (80% A4, 15% A3, 5% A5)
                    page_choice = random.choices(
                        self.page_sizes,
                        weights=[0.15, 0.80, 0.05],  # A3, A4, A5
                        k=1
                    )[0]
                    
                    # Generate quantity based on page size
                    if page_choice["size_name"] == "A4":
                        quantity = max(20, int(random.gauss(avg_additional, variance)))
                    elif page_choice["size_name"] == "A3":
                        quantity = max(10, int(random.gauss(avg_additional/2, variance/2)))
                    else:  # A5
                        quantity = max(40, int(random.gauss(avg_additional*2, variance)))
                    
                    multiplier = price_multipliers[page_choice["size_name"]]
                    amount = quantity * page_price * multiplier
                    method = weighted_choice(payment_methods)
                    reference = f"TXN{random.randint(100000, 999999)}"
                    status = 'completed' if random.random() < success_rate else random.choice(['failed', 'pending', 'refunded'])
                    transaction_date = random_date_in_range(365, 0)
                    
                    # Optionally link to a discount pack if quantity matches a pack
                    discount_pack_id = None
                    if hasattr(self, 'discount_packs') and self.discount_packs:
                        matching_pack = next(
                            (dp for dp in self.discount_packs if dp['num_pages'] == quantity),
                            None
                        )
                        if matching_pack:
                            discount_pack_id = matching_pack['discount_pack_id']
                    
                    bulk_purchases.add_row([
                        purchase_id, student['student_id'], page_choice["page_size_id"], 
                        quantity, amount, discount_pack_id, method, reference, status, 
                        transaction_date.strftime('%Y-%m-%d %H:%M:%S')
                    ])
        
        for stmt in bulk_purchases.get_statements():
            self.add_sql(stmt)
    
    def generate_discount_packs(self):
        """Generate discount packages for page purchases."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- DISCOUNT PACKAGES DATA")
        self.add_sql("-- ============================================")
        
        bulk = BulkInsertHelper("discount_pack", [
            "discount_pack_id", "num_pages", "percent_off", "pack_name",
            "description", "is_active", "created_at", "updated_at"
        ])
        
        # Default discount packages matching the spec requirements
        # Spec: 50 pages: $10.00, 100 pages: $18.00 (10% off), 200 pages: $35.00 (12.5% off), 500 pages: $80.00 (20% off)
        default_packs = [
            {"num_pages": 50, "percent_off": 0.0, "name": "50 pages", "desc": "50 pages: $10.00 ($0.200/page)"},
            {"num_pages": 100, "percent_off": 0.10, "name": "100 pages", "desc": "100 pages: $18.00 ($0.180/page) - 10% off"},
            {"num_pages": 200, "percent_off": 0.125, "name": "200 pages", "desc": "200 pages: $35.00 ($0.175/page) - 12.5% off"},
            {"num_pages": 500, "percent_off": 0.20, "name": "500 pages", "desc": "500 pages: $80.00 ($0.160/page) - 20% off"},
        ]
        
        # Use discount packs from spec if available, otherwise use defaults
        discount_packs = self.spec.get('discount_packs', default_packs)
        
        # Store discount packs for use in purchase generation
        self.discount_packs = []
        
        for pack_config in discount_packs:
            discount_pack_id = generate_uuid()
            num_pages = pack_config.get('num_pages', pack_config.get('pages', 100))
            percent_off = pack_config.get('percent_off', pack_config.get('discount', 0.05))
            
            pack_name = pack_config.get('name', pack_config.get('pack_name', f"{num_pages} Page Pack"))
            description = pack_config.get('description', pack_config.get('desc', f"Discount package: {percent_off*100:.0f}% off for {num_pages} pages"))
            is_active = pack_config.get('is_active', True)
            created_at = random_date_in_range(365, 30)
            updated_at = created_at
            
            pack_data = {
                'discount_pack_id': discount_pack_id,
                'num_pages': num_pages,
                'percent_off': percent_off
            }
            self.discount_packs.append(pack_data)
            
            bulk.add_row([
                discount_pack_id, num_pages, percent_off, pack_name,
                description, is_active, created_at.strftime('%Y-%m-%d %H:%M:%S'),
                updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        for stmt in bulk.get_statements():
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
        """Generate realistic print jobs with pages."""
        self.add_sql("\n-- ============================================")
        self.add_sql("-- PRINT JOBS DATA")
        self.add_sql("-- ============================================")
        
        # Debug: Show available page sizes
        if not hasattr(self, 'page_sizes') or not self.page_sizes:
            raise ValueError("Page sizes not generated yet. Ensure generate_page_allocation_system() runs before generate_print_jobs().")
        
        print(f"Available page sizes: {[ps['size_name'] for ps in self.page_sizes]}")
        
        avg_jobs = self.spec['avg_print_jobs_per_student']
        variance = self.spec['print_job_variance']
        
        # Get distributions
        file_type_dist = self.spec['file_types']
        paper_size_dist = self.spec['paper_size_distribution']
        orientation_dist = self.spec['orientation_distribution']
        print_side_dist = self.spec['print_side_distribution']
        color_mode_dist = self.spec['color_mode_distribution']
        status_dist = self.spec['print_status_distribution']
        copy_dist = self.spec['copy_distribution']
        
        # Activity patterns
        peak_hours = self.spec['peak_hours']
        normal_hours = self.spec['normal_hours']
        low_hours = self.spec['low_hours']
        
        hour_patterns = {
            'peak': peak_hours,
            'normal': normal_hours,
            'low': low_hours
        }
        
        # Document templates
        doc_templates = self.spec['document_name_templates']
        courses = self.spec['course_names']
        
        # Get enabled printers only
        enabled_printers = [p for p in self.printers if p['is_enabled']]
        
        # Use actual media files if available, otherwise generate names
        use_real_files = len(self.media_files) > 0
        
        bulk_jobs = BulkInsertHelper("print_job", [
            "job_id", "student_id", "printer_id", "file_name", "file_type",
            "file_size_kb", "paper_size_id", "page_orientation", "print_side",
            "color_mode", "number_of_copy", "print_status", "start_time",
            "end_time", "created_at"
        ])
        
        bulk_pages = BulkInsertHelper("print_job_page", [
            "page_record_id", "job_id", "page_number"
        ])
        
        job_id_counter = 1
        
        for student in self.students:
            num_jobs = max(0, int(random.gauss(avg_jobs, variance)))
            
            for _ in range(num_jobs):
                job_id = generate_uuid()
                
                # Select printer
                printer = random.choice(enabled_printers)
                
                # Generate file details
                file_ext = weighted_choice(file_type_dist)
                
                # Use actual media files or generate realistic names
                if use_real_files and random.random() < 0.3:  # 30% chance to use real file
                    # Filter media files by extension
                    matching_files = [f for f in self.media_files if f.lower().endswith(f'.{file_ext}')]
                    if matching_files:
                        file_name = random.choice(matching_files)
                        # Try to get actual file size if possible
                        try:
                            media_path = os.path.join(MEDIA_FOLDER, file_name)
                            if os.path.exists(media_path):
                                file_size_kb = os.path.getsize(media_path) // 1024
                                file_size_kb = max(1, file_size_kb)  # At least 1KB
                            else:
                                file_size_kb = random.randint(100, 10240)
                        except:
                            file_size_kb = random.randint(100, 10240)
                    else:
                        file_name = generate_document_name(doc_templates, courses, f".{file_ext}")
                        file_size_kb = random.randint(100, 10240)
                else:
                    file_name = generate_document_name(doc_templates, courses, f".{file_ext}")
                    # Realistic file sizes by type
                    if file_ext == 'pdf':
                        file_size_kb = random.randint(500, 5000)  # 500KB to 5MB
                    elif file_ext in ['jpg', 'png']:
                        file_size_kb = random.randint(200, 2000)  # 200KB to 2MB
                    elif file_ext == 'docx':
                        file_size_kb = random.randint(100, 1000)  # 100KB to 1MB
                    elif file_ext == 'xlsx':
                        file_size_kb = random.randint(50, 500)   # 50KB to 500KB
                    elif file_ext == 'pptx':
                        file_size_kb = random.randint(1000, 10000)  # 1MB to 10MB
                    else:
                        file_size_kb = random.randint(100, 1000)  # Default
                
                # Print settings
                paper_size_name = weighted_choice(paper_size_dist)
                
                # Find matching page size with fallback to A4
                matching_page_size = None
                for ps in self.page_sizes:
                    if ps["size_name"] == paper_size_name:
                        matching_page_size = ps
                        break
                
                if not matching_page_size:
                    # Fallback to A4 if the specified size doesn't exist
                    matching_page_size = next(
                        (ps for ps in self.page_sizes if ps["size_name"] == "A4"),
                        self.page_sizes[0] if self.page_sizes else None
                    )
                
                if not matching_page_size:
                    raise ValueError(f"No page sizes available. Available sizes: {[ps['size_name'] for ps in self.page_sizes]}")
                
                paper_size_id = matching_page_size["page_size_id"]
                orientation = weighted_choice(orientation_dist)
                print_side = weighted_choice(print_side_dist)
                color_mode = weighted_choice(color_mode_dist)
                num_copies = int(weighted_choice(copy_dist))
                status = weighted_choice(status_dist)
                
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
                
                # Generate pages
                avg_pages = self.spec['avg_pages_per_document']
                page_variance = self.spec['pages_variance']
                min_pages = self.spec['min_pages_per_job']
                max_pages = self.spec['max_pages_per_job']
                
                num_pages = max(min_pages, min(max_pages, int(random.gauss(avg_pages, page_variance))))
                
                job_data = {
                    'job_id': job_id,
                    'student_id': student['student_id'],
                    'printer_id': printer['printer_id'],
                    'num_pages': num_pages
                }
                
                self.print_jobs.append(job_data)
                
                bulk_jobs.add_row([
                    job_id, student['student_id'], printer['printer_id'],
                    file_name, file_ext, file_size_kb, paper_size_id,
                    orientation, print_side, color_mode, num_copies,
                    status,
                    start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                    end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None,
                    created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
                # Add pages for this job
                for page_num in range(1, num_pages + 1):
                    page_record_id = generate_uuid()
                    bulk_pages.add_row([page_record_id, job_id, page_num])
        
        for stmt in bulk_jobs.get_statements():
            self.add_sql(stmt)
        
        for stmt in bulk_pages.get_statements():
            self.add_sql(stmt)
    
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
            
            # Look up room and building information
            room = next((r for r in self.rooms if r['room_id'] == printer['room_id']), None)
            building = None
            if room:
                building = next((b for b in self.buildings if b['building_id'] == room['building_id']), None)
            
            building_name = building['building_name'] if building else printer.get('building_code', 'Unknown Building')
            room_code = printer.get('room_code', 'Unknown Room')
            
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
    
    # Generate data
    print("\n" + "=" * 70)
    print("GENERATING DATA (BULK INSERTS)")
    print("=" * 70)
    print()
    
    generator = PrintingServiceDataGenerator(spec, media_files)
    
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
        print(f"Classes generated: {len(generator.classes)}")
        print(f"Students generated: {len(generator.students)}")
        print(f"Staff generated: {len(generator.staff)}")
        print(f"Printers generated: {len(generator.printers)}")
        print(f"Print jobs generated: {len(generator.print_jobs)}")
        print(f"Output file: {OUTPUT_SQL_FILE}")
        print()
        print("Ready to import into database!")
        
    except Exception as e:
        print(f"Error during data generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
