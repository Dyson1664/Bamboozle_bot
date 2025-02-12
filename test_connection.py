import time
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables (ensure your .env has the correct DATABASE_URL)
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def test_query():
    start_time = time.time()
    try:
        # Connect to the database (ensure your DATABASE_URL uses the IPv4-compatible host)
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    elapsed = time.time() - start_time
    print(f"Elapsed time: {elapsed:.3f} seconds")

if __name__ == '__main__':
    test_query()
