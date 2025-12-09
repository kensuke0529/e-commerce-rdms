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
            # Validate environment variables
            if not all([self.host, self.port, self.database, self.user, self.password]):
                missing = []
                if not self.host:
                    missing.append("DB_HOST")
                if not self.port:
                    missing.append("DB_PORT")
                if not self.database:
                    missing.append("DB_NAME")
                if not self.user:
                    missing.append("DB_USER")
                if not self.password:
                    missing.append("DB_PASSWORD")
                error_msg = (
                    f"Missing database environment variables: {', '.join(missing)}"
                )
                print(f"-- Connection error: {error_msg} --")
                print(
                    f"-- Debug: host={self.host}, port={self.port}, database={self.database}, user={self.user}, password={'***' if self.password else 'None'} --"
                )
                raise ValueError(error_msg)

            self.conn = psycopg2.connect(
                database=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            self.cur = self.conn.cursor()
            return self.conn
        except psycopg2.Error as e:
            error_msg = f"PostgreSQL connection error: {str(e)}"
            print(f"-- Connection error: {error_msg} --")
            raise ConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Database connection error: {str(e)}"
            print(f"-- Connection error: {error_msg} --")
            raise ConnectionError(error_msg) from e

    def execute(self):
        if not self.cur:
            raise RuntimeError(
                "Database cursor not initialized. Call connect_to_db() first."
            )
        try:
            self.cur.execute(self.query)
            return self.cur.fetchall()

        except psycopg2.Error as e:
            error_msg = f"SQL execution error: {str(e)}"
            print(f"-- Error executing query: {error_msg} --")
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Query execution error: {str(e)}"
            print(f"-- Error executing query: {error_msg} --")
            raise RuntimeError(error_msg) from e

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    query = "SELECT * FROM product LIMIT 5;"

    db = query_executor(query)
    db.connect_to_db()

    results = db.execute()

    print("extract first row from product table")
    print(results[0])

    db.close()
