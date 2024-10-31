import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the DATABASE_URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def get_vocab(book, unit):
    """
    Retrieves vocabulary words from the 'vocab' table based on the book and unit.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cursor = conn.cursor()

        query = "SELECT word FROM vocab WHERE book = %s AND unit = %s"
        cursor.execute(query, (book.capitalize(), unit))
        results = cursor.fetchall()

        if not results:
            print('Not in Database')
            return []

        vocab_list = [word[0] for word in results]
        return vocab_list

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        if conn:
            cursor.close()
            conn.close()

def get_kg_vocab(level, title):
    """
    Retrieves kindergarten vocabulary words from the 'kindergarten' table based on the level and title.
    """
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
            conn.close()

def some_function():
    """
    Retrieves a dictionary mapping books to their units from the 'vocab' table.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return {}
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT book, unit FROM vocab")
        results = cur.fetchall()

        books_units = {}
        for book, unit in results:
            if book not in books_units:
                books_units[book] = [unit]
            else:
                books_units[book].append(unit)

        return books_units

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return {}

    finally:
        if conn:
            cur.close()
            conn.close()

def make_kg_dict():
    """
    Creates a dictionary of kindergarten vocabularies categorized by title.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return {}
        cursor = conn.cursor()

        query = 'SELECT DISTINCT title, vocab FROM kindergarten'
        cursor.execute(query)
        results = cursor.fetchall()

        kg_dict = {}
        for title, vocab in results:
            if title not in kg_dict:
                kg_dict[title] = [vocab]
            else:
                kg_dict[title].append(vocab)

        return kg_dict

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return {}

    finally:
        if conn:
            cursor.close()
            conn.close()

def get_all_books():
    """
    Retrieves a sorted list of all distinct book names from the 'vocab' table.
    """
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT book FROM vocab")
        books = [book[0] for book in cur.fetchall()]
        books.sort()

        return books

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        if conn:
            cur.close()
            conn.close()

def create_login_db():
    """
    Creates the 'users' table if it does not exist.
    """
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
            conn.close()

# If you have any functions that insert data into the database, update them as well
def enter_vocab_to_database(vocab_words):
    """
    Inserts vocabulary words into the 'vocab' table.
    """
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
            conn.close()

def enter_kg_vocab_to_database(kg_vocab):
    """
    Inserts kindergarten vocabulary into the 'kindergarten' table.
    """
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
            conn.close()

def remove_duplicates():
    """
    Removes duplicate entries from the 'vocab' table.
    """
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
            conn.close()

# If you have user-related functions that need updating
from werkzeug.security import generate_password_hash

def add_user(username, password, personal_email, bamboozle_email, bamboozle_password):
    """
    Adds a new user to the 'users' table.
    """
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
            conn.close()

# If you need to drop tables (use with caution)
def drop_table(table_name):
    """
    Drops the specified table from the database.
    """
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
            conn.close()

# Example usage of drop_table function
# drop_table('users')

if __name__ == '__main__':
    # Example: Create tables if they don't exist
    # create_login_db()
    # You can call other functions here for testing
    pass
