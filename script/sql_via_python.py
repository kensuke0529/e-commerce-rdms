import os 
import pandas as pd
from dotenv import load_dotenv
import psycopg2

load_dotenv()


class query_executor:
    def __init__(self, query):
        self.conn = None
        self.cur = None
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.query = query
        
    def connect_to_db(self):
        try: 
            self.conn = psycopg2.connect(
                database=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cur = self.conn.cursor()  
            print('-- Connected to the database --')
            return self.conn
        except Exception as e:
            print(f'-- Connection error: {e} --') 
            return None
        
    def execute(self):
        try:
            self.cur.execute(self.query)
            return self.cur.fetchall()
        
        except Exception as e:
            print(f'-- Error executing query: {e} --')
            return None
        
    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            print('-- Connection closed --')


if __name__ == "__main__":
    
    query = "SELECT * FROM product LIMIT 5;"

    db = query_executor(query)
    db.connect_to_db()
    
    results = db.execute()
    
    print('extract first row from product table')
    print(results[0])
    
    db.close()
