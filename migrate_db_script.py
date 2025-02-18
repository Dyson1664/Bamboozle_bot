import sqlite3
import psycopg2
import os

# Load environment variables from .env file (if you're using one)
from dotenv import load_dotenv
load_dotenv()

# Connect to SQLite database
sqlite_conn = sqlite3.connect('vocabulary.db2')
sqlite_cur = sqlite_conn.cursor()

# Connect to PostgreSQL database on Heroku
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL not found in environment variables.")

pg_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
pg_cur = pg_conn.cursor()

# Function to migrate 'vocab' table
def migrate_vocab():
    sqlite_cur.execute("SELECT id, book, unit, word FROM vocab")
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            "INSERT INTO vocab (id, book, unit, word) VALUES (%s, %s, %s, %s)",
            row
        )
    pg_conn.commit()
    print("Migrated 'vocab' table.")

# Function to migrate 'kindergarten' table
def migrate_kindergarten():
    sqlite_cur.execute("SELECT id, level, title, vocab FROM kindergarten")
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            "INSERT INTO kindergarten (id, level, title, vocab) VALUES (%s, %s, %s, %s)",
            row
        )
    pg_conn.commit()
    print("Migrated 'kindergarten' table.")

# Function to migrate 'users' table
def migrate_users():
    sqlite_cur.execute("SELECT id, username, password, personal_email, bamboozle_email, bamboozle_password FROM users")
    rows = sqlite_cur.fetchall()
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO users (id, username, password, personal_email, bamboozle_email, bamboozle_password)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            row
        )
    pg_conn.commit()
    print("Migrated 'users' table.")

# Call migration functions
try:
    migrate_vocab()
    migrate_kindergarten()
    migrate_users()
    print("Data migration completed successfully.")
except Exception as e:
    print(f"An error occurred during migration: {e}")
finally:
    # Close all connections
    sqlite_conn.close()
    pg_conn.close()


