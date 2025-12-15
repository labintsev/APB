import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_sqlite_to_excel(db_path, excel_path=None):
    """
    Export all tables from SQLite database to Excel file (multiple sheets)
    
    Args:
        db_path: Path to SQLite database file
        excel_path: Path for output Excel file (optional)
    """
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    
    # Get all table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    if not tables:
        print("No tables found in the database!")
        return
    
    # Generate output filename if not provided
    if excel_path is None:
        db_name = os.path.splitext(os.path.basename(db_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = f"{db_name}_export_{timestamp}.xlsx"
    
    # Create Excel writer
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for table in tables:
            table_name = table[0]
            try:
                # Read table into pandas DataFrame
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql_query(query, conn)
                
                # Write to Excel sheet
                df.to_excel(writer, sheet_name=table_name, index=False)
                print(f"✓ Table '{table_name}' exported ({len(df)} rows)")
                
            except Exception as e:
                print(f"✗ Error exporting table '{table_name}': {e}")
    
    conn.close()
    print(f"\n✅ All tables exported to: {excel_path}")

# Alternative: Export to separate Excel files
def export_sqlite_to_multiple_excel(db_path, output_dir='exports'):
    """
    Export each table to separate Excel files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, conn)
            
            # Clean table name for filename
            safe_name = "".join(c for c in table_name if c.isalnum() or c in (' ', '_')).rstrip()
            output_path = os.path.join(output_dir, f"{safe_name}.xlsx")
            
            df.to_excel(output_path, index=False)
            print(f"✓ Table '{table_name}' exported to: {output_path}")
            
        except Exception as e:
            print(f"✗ Error exporting table '{table_name}': {e}")
    
    conn.close()

# Usage examples
if __name__ == "__main__":
    # Example 1: Export all tables to single Excel file
    db_file = "broadcast_target.db"  # Change to your database file
    if os.path.exists(db_file):
        export_sqlite_to_excel(db_file)
    
