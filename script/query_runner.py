import csv
import os
import pandas as pd
from sql_via_python import query_executor

class SQLAnalysisRunner:
    """Run SQL analysis files and display results."""
    
    def __init__(self, sql_directory="../sql"):
        self.sql_dir = sql_directory
    
    def read_sql_file(self, filename):
        """Read SQL file and extract queries."""
        filepath = os.path.join(self.sql_dir, filename)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split by semicolon to get individual queries
        queries = [q.strip() for q in content.split(';') if q.strip()]
        return queries
    
    def run_analysis_file(self, filename, csv_export=None, file_name=None):        
        queries = self.read_sql_file(filename)
        
        for i, query in enumerate(queries, 1):
            # Remove comment lines from the query block
            lines = query.split('\n')
            sql_lines = [line for line in lines if not line.strip().startswith('--')]
            clean_query = '\n'.join(sql_lines).strip()
            
            # Skip if nothing left after removing comments
            if not clean_query:
                continue
            
            print(f"\n  Query {i}:")
            
            # Execute query
            db = query_executor(clean_query)
            db.connect_to_db()
            results = db.execute()
            
            if results:
                columns = [desc[0] for desc in db.cur.description]
                
                # Convert to DataFrame with column names
                df = pd.DataFrame(results, columns=columns)
                print(df)
                
                if csv_export:
                    df.to_csv(f'../result/{file_name}.csv')
                    print('new csv file exported')
                    
            else:
                print("No results returned\n")
            
            db.close()

if __name__ == "__main__":
    runner = SQLAnalysisRunner()
    
    runner.run_analysis_file("1.revenue_analysis.sql", csv_export=True, file_name='sql_query_result')
    # runner.run_analysis_file("2.customer_analysis.sql")
    # runner.run_analysis_file("3.product_analysis.sql")