import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to PostgreSQL database on Heroku
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in environment variables.")

try:
    pg_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    pg_cur = pg_conn.cursor()

    # Create 'vocab' table
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS vocab (
            id SERIAL PRIMARY KEY,
            book TEXT NOT NULL,
            unit INTEGER NOT NULL,
            word TEXT NOT NULL
        );
    ''')

    # Create 'kindergarten' table
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS kindergarten (
            id SERIAL PRIMARY KEY,
            level TEXT NOT NULL,
            title TEXT NOT NULL,
            vocab TEXT NOT NULL
        );
    ''')

    # Create 'users' table
    pg_cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            personal_email TEXT NOT NULL UNIQUE,
            bamboozle_email TEXT,
            bamboozle_password TEXT
        );
    ''')

    pg_conn.commit()
    print("Tables created successfully.")

except Exception as e:
    print(f"An error occurred while creating tables: {e}")
finally:
    if 'pg_cur' in locals():
        pg_cur.close()
    if 'pg_conn' in locals():
        pg_conn.close()
