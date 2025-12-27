#!/usr/bin/env python3
"""
Execute SQL file against Azure SQL Database and return results
"""

import pyodbc
import sys
import os
from pathlib import Path
from typing import List, Tuple, Any, Optional

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


def read_sql_file(file_path: str) -> str:
    """
    Read SQL file content
    
    Args:
        file_path: Path to SQL file
        
    Returns:
        SQL content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading SQL file: {e}")


def split_sql_statements(sql_content: str) -> List[str]:
    """
    Split SQL content into individual statements
    Handles GO separators and semicolons
    
    Args:
        sql_content: Full SQL content
        
    Returns:
        List of SQL statements
    """
    # Remove comments (-- style)
    lines = []
    for line in sql_content.split('\n'):
        if '--' in line:
            line = line[:line.index('--')]
        lines.append(line)
    sql_content = '\n'.join(lines)
    
    # Split by GO (case insensitive)
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line_stripped = line.strip()
        if line_stripped.upper() == 'GO':
            if current_statement:
                stmt = '\n'.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
        else:
            current_statement.append(line)
    
    # Add remaining statement
    if current_statement:
        stmt = '\n'.join(current_statement).strip()
        if stmt:
            statements.append(stmt)
    
    return statements


def execute_statement(cursor: pyodbc.Cursor, statement: str, statement_num: int = None) -> Tuple[bool, Optional[List[Tuple[Any, ...]]], Optional[List[str]], Optional[str]]:
    """
    Execute a single SQL statement
    
    Args:
        cursor: Database cursor
        statement: SQL statement to execute
        statement_num: Statement number (for logging)
        
    Returns:
        Tuple of (success, results, columns, error_message)
    """
    try:
        # Skip empty statements
        if not statement.strip():
            return True, None, None, None
        
        # Execute statement
        cursor.execute(statement)
        
        # Check if it's a SELECT statement (returns results)
        if cursor.description:
            # It's a SELECT - fetch results
            results = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            
            # Convert to list of tuples
            result_list = []
            for row in results:
                result_list.append(row)
            
            return True, result_list, columns, None
        else:
            # It's an INSERT/UPDATE/DELETE/etc - return rowcount
            rowcount = cursor.rowcount
            return True, [(f"Rows affected: {rowcount}",)], None, None
            
    except pyodbc.Error as e:
        error_msg = f"SQL Error: {e}"
        return False, None, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        return False, None, None, error_msg


def print_results(results: List[Tuple[Any, ...]], columns: List[str] = None, max_rows: int = 100):
    """
    Print query results in formatted table
    
    Args:
        results: List of result rows
        columns: Column names (optional)
        max_rows: Maximum rows to print
    """
    if not results:
        print("  No results returned.")
        return
    
    # If first row is a string (like "Rows affected"), just print it
    if len(results) > 0 and isinstance(results[0], tuple) and len(results[0]) == 1 and isinstance(results[0][0], str) and "Rows affected" in results[0][0]:
        print(f"  {results[0][0]}")
        return
    
    # Determine columns from first row if not provided
    if columns is None and results:
        num_cols = len(results[0]) if results else 0
        columns = [f"Column_{i+1}" for i in range(num_cols)]
    
    if not columns:
        return
    
    # Calculate column widths
    col_widths = []
    for i, col in enumerate(columns):
        max_width = len(col)
        for row in results[:max_rows]:
            if i < len(row):
                val_str = str(row[i]) if row[i] is not None else "NULL"
                max_width = max(max_width, min(len(val_str), 30))  # Cap at 30 chars
        col_widths.append(max(max_width, 10))  # Minimum width 10
    
    # Print header
    header_parts = []
    for i, col in enumerate(columns):
        header_parts.append(f"{col:<{col_widths[i]}}")
    header_line = " | ".join(header_parts)
    print(f"  {header_line}")
    
    # Print separator
    separator_line = "-" * len(header_line)
    print(f"  {separator_line}")
    
    # Print rows
    rows_printed = 0
    for row in results:
        if rows_printed >= max_rows:
            print(f"  ... and {len(results) - max_rows} more rows")
            break
        
        # Format row values
        formatted_parts = []
        for i, val in enumerate(row):
            if val is None:
                val_str = "NULL"
            else:
                val_str = str(val)
                if len(val_str) > col_widths[i]:
                    val_str = val_str[:col_widths[i]-3] + "..."
            formatted_parts.append(f"{val_str:<{col_widths[i]}}")
        
        print("  " + " | ".join(formatted_parts))
        rows_printed += 1
    
    print(f"  Total rows: {len(results)}")


def execute_sql_file(file_path: str, verbose: bool = True) -> dict:
    """
    Execute SQL file and return results
    
    Args:
        file_path: Path to SQL file
        verbose: Whether to print detailed output
        
    Returns:
        Dictionary with execution results
    """
    # Resolve file path
    if not os.path.isabs(file_path):
        # Relative path - try from current directory and pipeline directory
        base_dir = Path(__file__).parent.parent
        full_path = base_dir / file_path
        if not full_path.exists():
            full_path = Path(file_path)
    else:
        full_path = Path(file_path)
    
    if not full_path.exists():
        return {
            'success': False,
            'error': f"File not found: {full_path}",
            'statements_executed': 0,
            'statements_succeeded': 0,
            'statements_failed': 0
        }
    
    if verbose:
        print("="*80)
        print("EXECUTING SQL FILE")
        print("="*80)
        print(f"File: {full_path}")
        print("="*80)
    
    # Read SQL file
    try:
        sql_content = read_sql_file(str(full_path))
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'statements_executed': 0,
            'statements_succeeded': 0,
            'statements_failed': 0
        }
    
    # Split into statements
    statements = split_sql_statements(sql_content)
    
    if verbose:
        print(f"\nFound {len(statements)} SQL statement(s) to execute\n")
    
    # Connect to database
    try:
        if verbose:
            print("Connecting to database...")
        conn = pyodbc.connect(CONNECTION_STRING, timeout=30)
        cursor = conn.cursor()
        if verbose:
            print("✓ Connected successfully\n")
    except Exception as e:
        return {
            'success': False,
            'error': f"Connection failed: {e}",
            'statements_executed': 0,
            'statements_succeeded': 0,
            'statements_failed': 0
        }
    
    # Execute statements
    results_summary = {
        'success': True,
        'statements_executed': 0,
        'statements_succeeded': 0,
        'statements_failed': 0,
        'results': [],
        'errors': []
    }
    
    try:
        for i, statement in enumerate(statements, 1):
            if verbose:
                print(f"{'='*80}")
                print(f"STATEMENT {i}/{len(statements)}")
                print(f"{'='*80}")
                # Show first 200 chars of statement
                stmt_preview = statement.strip()[:200]
                if len(statement) > 200:
                    stmt_preview += "..."
                print(f"SQL: {stmt_preview}\n")
            
            results_summary['statements_executed'] += 1
            
            success, results, columns, error = execute_statement(cursor, statement, i)
            
            if success:
                results_summary['statements_succeeded'] += 1
                if verbose:
                    if results:
                        print_results(results, columns)
                    else:
                        print("  Statement executed successfully (no results returned)")
                
                results_summary['results'].append({
                    'statement_num': i,
                    'success': True,
                    'results': results,
                    'columns': columns
                })
            else:
                results_summary['statements_failed'] += 1
                results_summary['success'] = False
                if verbose:
                    print(f"  ✗ ERROR: {error}")
                
                results_summary['errors'].append({
                    'statement_num': i,
                    'error': error,
                    'statement': statement[:500]  # First 500 chars
                })
            
            if verbose:
                print()
        
        # Commit transaction
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        results_summary['success'] = False
        results_summary['errors'].append({
            'statement_num': 'unknown',
            'error': f"Transaction error: {e}",
            'statement': None
        })
        if verbose:
            print(f"\n✗ Transaction rolled back due to error: {e}")
    
    finally:
        cursor.close()
        conn.close()
        if verbose:
            print("="*80)
            print("EXECUTION SUMMARY")
            print("="*80)
            print(f"Statements executed: {results_summary['statements_executed']}")
            print(f"Statements succeeded: {results_summary['statements_succeeded']}")
            print(f"Statements failed: {results_summary['statements_failed']}")
            if results_summary['success']:
                print("✓ All statements executed successfully!")
            else:
                print("✗ Some statements failed")
            print("="*80)
    
    return results_summary


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("="*80)
        print("ERROR: No SQL file specified")
        print("="*80)
        print("\nUsage: python execute_sql_file.py <path_to_sql_file>")
        print("\nExamples:")
        print("  python execute_sql_file.py ../sql/design.sql")
        print("  python execute_sql_file.py ../sql/insert.sql")
        print("  python execute_sql_file.py test_query.sql")
        print("\nThe script will:")
        print("  1. Connect to Azure SQL Database")
        print("  2. Read and execute the SQL file")
        print("  3. Display results in the console")
        print("="*80)
        sys.exit(1)
    
    file_path = sys.argv[1]
    results = execute_sql_file(file_path, verbose=True)
    
    # Exit with error code if any statements failed
    if not results['success']:
        print(f"\n⚠️  Execution completed with {results['statements_failed']} failed statement(s)")
        sys.exit(1)
    else:
        print(f"\n✅ Execution completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()

