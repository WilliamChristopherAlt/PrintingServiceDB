#!/usr/bin/env python3
"""
Test script to connect to Azure SQL Database and execute test queries
"""

import pyodbc
import sys
from typing import List, Tuple, Any

# Connection string
CONNECTION_STRING = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:lgbbq.database.windows.net,1433;"
    "Database=lgbbq;"
    "Uid=lqbbq;"
    "Pwd=ptpm@2025;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

# Test SQL queries
TEST_QUERIES = [
    # Test 1: Check connection and get database version
    "SELECT @@VERSION AS SQLServerVersion",
    
    # Test 2: Check if tables exist
    """
    SELECT 
        TABLE_SCHEMA,
        TABLE_NAME,
        TABLE_TYPE
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_SCHEMA, TABLE_NAME
    """,
    
    # Test 3: Count records in key tables
    """
    SELECT 
        'user' AS table_name,
        COUNT(*) AS record_count
    FROM [user]
    UNION ALL
    SELECT 'student', COUNT(*) FROM student
    UNION ALL
    SELECT 'printer_physical', COUNT(*) FROM printer_physical
    UNION ALL
    SELECT 'print_job', COUNT(*) FROM print_job
    UNION ALL
    SELECT 'deposit', COUNT(*) FROM deposit
    UNION ALL
    SELECT 'payment', COUNT(*) FROM payment
    """,
    
    # Test 4: Check page size prices
    """
    SELECT 
        ps.size_name,
        psp.page_price,
        psp.is_active
    FROM page_size_price psp
    JOIN page_size ps ON psp.page_size_id = ps.page_size_id
    ORDER BY ps.size_name
    """,
    
    # Test 5: Check color mode prices (will be handled dynamically)
    None,  # Will be replaced with dynamic query
    
    # Test 6: Sample student balance
    """
    SELECT TOP 5
        s.student_code,
        u.full_name,
        u.email,
        sbv.balance_amount
    FROM student_balance_view sbv
    JOIN student s ON sbv.student_id = s.student_id
    JOIN [user] u ON s.user_id = u.user_id
    ORDER BY sbv.balance_amount DESC
    """
]


def check_column_exists(cursor: pyodbc.Cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        query = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
        """
        cursor.execute(query, table_name, column_name)
        return cursor.fetchone()[0] > 0
    except:
        return False


def execute_query(cursor: pyodbc.Cursor, query: str, description: str) -> List[Tuple[Any, ...]]:
    """
    Execute a SQL query and return results
    
    Args:
        cursor: Database cursor
        query: SQL query string
        description: Description of the query
        
    Returns:
        List of tuples containing query results
    """
    try:
        print(f"\n{'='*80}")
        print(f"QUERY: {description}")
        print(f"{'='*80}")
        print(f"SQL: {query.strip()[:100]}..." if len(query) > 100 else f"SQL: {query.strip()}")
        print(f"{'-'*80}")
        
        cursor.execute(query)
        
        # Get column names
        columns = [column[0] for column in cursor.description]
        
        # Print header
        print(" | ".join(f"{col:<20}" for col in columns))
        print("-" * 80)
        
        # Fetch and print results
        results = []
        row_count = 0
        for row in cursor.fetchall():
            results.append(row)
            row_count += 1
            # Print row (limit to first 20 rows for display)
            if row_count <= 20:
                print(" | ".join(f"{str(val):<20}"[:20] for val in row))
        
        if row_count > 20:
            print(f"... and {row_count - 20} more rows")
        
        print(f"\nTotal rows: {row_count}")
        
        return results
        
    except Exception as e:
        print(f"ERROR executing query: {e}")
        return []


def main():
    """Main function to test database connection and execute queries"""
    
    print("="*80)
    print("AZURE SQL DATABASE CONNECTION TEST")
    print("="*80)
    print(f"Connecting to: lgbbq.database.windows.net")
    print(f"Database: lgbbq")
    print("="*80)
    
    try:
        # Connect to database
        print("\nAttempting to connect...")
        conn = pyodbc.connect(CONNECTION_STRING, timeout=30)
        print("✓ Connection successful!")
        
        cursor = conn.cursor()
        
        # Execute test queries
        query_descriptions = [
            "Database Version",
            "List All Tables",
            "Record Counts in Key Tables",
            "Page Size Prices",
            "Color Mode Prices",
            "Top 5 Students by Balance"
        ]
        
        for i, (query, description) in enumerate(zip(TEST_QUERIES, query_descriptions), 1):
            # Handle dynamic query for color mode prices
            if query is None and i == 5:
                # Check which column exists
                if check_column_exists(cursor, 'color_mode_price', 'price_multiplier'):
                    query = """
                    SELECT 
                        cm.color_mode_name,
                        cmp.price_multiplier AS price_value,
                        cmp.is_active
                    FROM color_mode_price cmp
                    JOIN color_mode cm ON cmp.color_mode_id = cm.color_mode_id
                    ORDER BY cm.color_mode_name
                    """
                elif check_column_exists(cursor, 'color_mode_price', 'price_per_page'):
                    query = """
                    SELECT 
                        cm.color_mode_name,
                        cmp.price_per_page AS price_value,
                        cmp.is_active
                    FROM color_mode_price cmp
                    JOIN color_mode cm ON cmp.color_mode_id = cm.color_mode_id
                    ORDER BY cm.color_mode_name
                    """
                else:
                    print(f"\n{'='*80}")
                    print(f"QUERY: {i}. {description}")
                    print(f"{'='*80}")
                    print("ERROR: Neither price_multiplier nor price_per_page column found")
                    continue
            
            if query:
                execute_query(cursor, query, f"{i}. {description}")
        
        # Close connection
        cursor.close()
        conn.close()
        print(f"\n{'='*80}")
        print("✓ All queries executed successfully!")
        print("✓ Connection closed")
        print("="*80)
        
    except pyodbc.Error as e:
        print(f"\n✗ Database connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Check if ODBC Driver 18 for SQL Server is installed")
        print("2. Verify connection string parameters")
        print("3. Check firewall rules for Azure SQL Database")
        print("4. Verify username and password")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

