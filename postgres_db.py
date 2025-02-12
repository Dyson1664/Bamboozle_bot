import os
import psycopg2
from psycopg2 import sql
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables
load_dotenv()

# Get the DATABASE_URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

# Create a global connection pool (adjust minconn and maxconn as needed)
pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL, sslmode='require')

def get_db_connection():
    """
    Retrieves a connection from the pool.
    """
    try:
        conn = pool.getconn()
        return conn
    except psycopg2.Error as e:
        print(f"Error getting connection from pool: {e}")
        return None

def release_db_connection(conn):
    """
    Returns a connection back to the pool.
    """
    if conn:
        pool.putconn(conn)


import time


def get_vocab(book, unit):
    """
    Retrieves vocabulary words from the 'vocab' table based on the book and unit.
    """
    total_start = time.time()
    conn = None
    try:
        # Measure time to obtain a connection
        t0 = time.time()
        conn = get_db_connection()
        t1 = time.time()
        print(f"Time to get connection: {t1 - t0:.3f} seconds")
        if conn is None:
            return []

        # Measure time to create a cursor
        t2 = time.time()
        cursor = conn.cursor()
        t3 = time.time()
        print(f"Time to create cursor: {t3 - t2:.3f} seconds")

        # Measure time to execute the query
        query = "SELECT word FROM vocab WHERE book = %s AND unit = %s"
        t4 = time.time()
        cursor.execute(query, (book.capitalize(), unit))
        t5 = time.time()
        print(f"Time to execute query: {t5 - t4:.3f} seconds")

        # Measure time to fetch the results
        results = cursor.fetchall()
        t6 = time.time()
        print(f"Time to fetch results: {t6 - t5:.3f} seconds")

        if not results:
            print('Not in Database')
            return []

        vocab_list = [word[0] for word in results]
        total_end = time.time()
        print(f"Total time in get_vocab: {total_end - total_start:.3f} seconds")
        return vocab_list
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            release_db_connection(conn)


def get_kg_vocab(level, title):
    """
    Retrieves kindergarten vocabulary words from the 'kindergarten' table based on the level and title.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cursor = conn.cursor()
        query = 'SELECT vocab FROM kindergarten WHERE level = %s AND title = %s'
        cursor.execute(query, (level, title))
        results = cursor.fetchall()
        vocab_list = [item[0] for item in results]
        print(f"{title}: {vocab_list}")
        return vocab_list
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            release_db_connection(conn)


import time
from psycopg2 import DatabaseError


def setup_function_combined():
    """
    Retrieves three sets of data using a single connection:
      1. A dictionary mapping books to their units (from the 'vocab' table).
      2. A sorted list of all distinct book names (from the 'vocab' table).
      3. A dictionary of kindergarten vocabularies grouped by title (from the 'kindergarten' table).

    Returns:
        tuple: (books_units, books, kg_dict)
            - books_units: dict mapping each book to a list of units.
            - books: sorted list of distinct book names.
            - kg_dict: dictionary mapping kindergarten titles to a list of vocabulary entries.
    """
    start = time.time()
    conn = get_db_connection()
    if conn is None:
        return {}, [], {}
    try:
        cur = conn.cursor()

        # Query 1: Get book-to-units mapping from the vocab table
        cur.execute("SELECT DISTINCT book, unit FROM vocab")
        results = cur.fetchall()
        books_units = {}
        for book, unit in results:
            if book not in books_units:
                books_units[book] = [unit]
            else:
                books_units[book].append(unit)
        for book in books_units:
            books_units[book].sort()

        # Query 2: Get a sorted list of all distinct books
        cur.execute("SELECT DISTINCT book FROM vocab")
        books = [row[0] for row in cur.fetchall()]
        books.sort()

        # Query 3: Get kindergarten vocabulary grouped by title
        cur.execute("SELECT DISTINCT title, vocab FROM kindergarten")
        results = cur.fetchall()
        kg_dict = {}
        for title, vocab in results:
            if title not in kg_dict:
                kg_dict[title] = [vocab]
            else:
                kg_dict[title].append(vocab)
        kg_dict = dict(sorted(kg_dict.items()))

        total_time = time.time() - start
        print(f"Combined setup_function took: {total_time:.3f} seconds")
        return books_units, books, kg_dict

    except DatabaseError as e:
        print(f"An error occurred in setup_function_combined: {e}")
        return {}, [], {}
    finally:
        cur.close()
        release_db_connection(conn)


def create_login_db():
    """
    Creates the 'users' table if it does not exist.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        insertion = '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            personal_email TEXT NOT NULL UNIQUE,
            bamboozle_email TEXT,
            bamboozle_password TEXT
        );
        '''
        cur.execute(insertion)
        conn.commit()
        print('Users table created')
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cur.close()
            release_db_connection(conn)

def enter_vocab_to_database(vocab_words):
    """
    Inserts vocabulary words into the 'vocab' table.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        insert_query = 'INSERT INTO vocab (book, unit, word) VALUES (%s, %s, %s)'
        cursor.executemany(insert_query, vocab_words)
        conn.commit()
        print('Vocabulary words inserted successfully.')
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cursor.close()
            release_db_connection(conn)

def enter_kg_vocab_to_database(kg_vocab):
    """
    Inserts kindergarten vocabulary into the 'kindergarten' table.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        insert_query = 'INSERT INTO kindergarten (level, title, vocab) VALUES (%s, %s, %s)'
        cursor.executemany(insert_query, kg_vocab)
        conn.commit()
        print('Kindergarten vocabulary inserted successfully.')
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cursor.close()
            release_db_connection(conn)

def remove_duplicates():
    """
    Removes duplicate entries from the 'vocab' table.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        delete_query = '''
        DELETE FROM vocab
        WHERE ctid NOT IN (
            SELECT min(ctid)
            FROM vocab
            GROUP BY book, unit, word
        );
        '''
        cursor.execute(delete_query)
        conn.commit()
        print('Duplicate entries removed.')
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cursor.close()
            release_db_connection(conn)

def add_user(username, password, personal_email, bamboozle_email, bamboozle_password):
    """
    Adds a new user to the 'users' table.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        hashed_password = generate_password_hash(password)
        insert_query = '''
        INSERT INTO users (username, password, personal_email, bamboozle_email, bamboozle_password)
        VALUES (%s, %s, %s, %s, %s)
        '''
        cur.execute(insert_query, (username, hashed_password, personal_email, bamboozle_email, bamboozle_password))
        conn.commit()
        print('User added successfully.')
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            cur.close()
            release_db_connection(conn)

def drop_table(table_name):
    """
    Drops the specified table from the database.
    """
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        drop_query = sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
        cur.execute(drop_query)
        conn.commit()
        print(f"Table '{table_name}' dropped successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred while dropping the table: {e}")
    finally:
        if conn:
            cur.close()
            release_db_connection(conn)

# Example usage of drop_table function
# drop_table('users')

if __name__ == '__main__':
    # Example: Create tables if they don't exist
    # create_login_db()
    # You can call other functions here for testing
    make_kg_dict()
    pass
