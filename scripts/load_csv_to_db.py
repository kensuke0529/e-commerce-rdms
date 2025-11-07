import os
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from io import StringIO

load_dotenv()


class CSVLoader:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        
        # Define loading order (respecting foreign key dependencies)
        self.load_order = [
            'department',
            'staff',
            'seller',
            'customer',
            'app_user',
            'product',
            'bid',
            'shipping',
            'order_header',
            'payment',
            'order_history',
            'import_distribution',
            'export_distribution',
            'customer_service',
            'seller_service',
            'customer_review',
            'seller_review'
        ]
        
    def connect_to_db(self):
        """Connect to PostgreSQL database"""
        try: 
            self.conn = psycopg2.connect(
                database=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cur = self.conn.cursor()  
            print('✓ Connected to the database')
            return True
        except Exception as e:
            print(f'✗ Connection error: {e}')
            return False
    
    def truncate_tables(self):
        """Clear all existing data from tables in reverse order"""
        print("\n🗑️  Clearing existing data...")
        try:
            # Reverse order for deletion (child tables first)
            for table in reversed(self.load_order):
                self.cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"  ✓ Cleared {table}")
            self.conn.commit()
            print("✓ All tables cleared successfully")
            return True
        except Exception as e:
            print(f"✗ Error truncating tables: {e}")
            self.conn.rollback()
            return False
    
    def load_csv_to_table(self, table_name, csv_path):
        """Load CSV file into specified table using COPY command"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            # Normalize column names to lowercase (PostgreSQL convention)
            df.columns = df.columns.str.lower()
            
            # Convert float columns that should be integers back to integers
            # This handles the case where pandas reads nullable integer columns as float64
            for col in df.columns:
                if df[col].dtype == 'float64':
                    # Check if all non-null values are whole numbers
                    non_null_values = df[col].dropna()
                    if len(non_null_values) > 0 and all(non_null_values == non_null_values.astype(int)):
                        # Convert to Int64 (nullable integer type)
                        df[col] = df[col].astype('Int64')
            
            # Get column names from CSV
            columns = df.columns.tolist()
            
            # Create a StringIO buffer
            buffer = StringIO()
            df.to_csv(buffer, index=False, header=False, na_rep='\\N')
            buffer.seek(0)
            
            # Use COPY command for efficient bulk loading with NULL handling
            copy_sql = f"COPY {table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')"
            self.cur.copy_expert(sql=copy_sql, file=buffer)
            
            self.conn.commit()
            return len(df)
            
        except Exception as e:
            print(f"  ✗ Error loading {table_name}: {e}")
            self.conn.rollback()
            return 0
    
    def load_all_csvs(self, data_dir):
        """Load all CSV files in the correct order"""
        print("\n📥 Loading CSV data into database...")
        print("=" * 70)
        
        total_rows = 0
        successful_tables = 0
        
        for table_name in self.load_order:
            csv_file = os.path.join(data_dir, f"{table_name}.csv")
            
            if not os.path.exists(csv_file):
                print(f"  ⚠ Skipping {table_name} (file not found)")
                continue
            
            rows = self.load_csv_to_table(table_name, csv_file)
            if rows > 0:
                print(f"  ✓ Loaded {table_name:<25} {rows:>6} rows")
                total_rows += rows
                successful_tables += 1
            else:
                print(f"  ✗ Failed to load {table_name}")
        
        print("=" * 70)
        print(f"✅ Successfully loaded {successful_tables} tables with {total_rows} total rows")
        return successful_tables, total_rows
    
    def verify_data(self):
        """Verify data was loaded correctly"""
        print("\n🔍 Verifying data integrity...")
        print("-" * 70)
        
        try:
            for table_name in self.load_order:
                self.cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = self.cur.fetchone()[0]
                print(f"  {table_name:<25} {count:>6} rows")
            
            # Run data quality checks
            print("\n📊 Data Quality Checks:")
            print("-" * 70)
            self.cur.execute("SELECT * FROM vw_data_quality_check;")
            checks = self.cur.fetchall()
            
            all_clean = True
            for check_name, issue_count in checks:
                status = "✓" if issue_count == 0 else "✗"
                print(f"  {status} {check_name:<25} {issue_count:>6} issues")
                if issue_count > 0:
                    all_clean = False
            
            if all_clean:
                print("\n✅ All data quality checks passed!")
            else:
                print("\n⚠️  Some data quality issues detected")
                
        except Exception as e:
            print(f"✗ Error verifying data: {e}")
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print('\n✓ Connection closed')


def main():
    """Main execution function"""
    print("=" * 70)
    print("CSV TO DATABASE LOADER")
    print("=" * 70)
    
    # Get the data directory path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, 'data')
    
    print(f"Data directory: {data_dir}")
    
    # Initialize loader
    loader = CSVLoader()
    
    # Connect to database
    if not loader.connect_to_db():
        return
    
    # Clear existing data
    if not loader.truncate_tables():
        loader.close()
        return
    
    # Load CSV data
    successful_tables, total_rows = loader.load_all_csvs(data_dir)
    
    if successful_tables > 0:
        # Verify the loaded data
        loader.verify_data()
    
    # Close connection
    loader.close()
    
    print("\n" + "=" * 70)
    print("✅ CSV LOADING COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    main()

