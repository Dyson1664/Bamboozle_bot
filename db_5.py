import sqlite3
import psycopg2


def create_db():
    conn = sqlite3.connect('vocabulary.db2')
    cursor = conn.cursor()
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS vocab (
        id INTEGER PRIMARY KEY,
        book TEXT NOT NULL,
        unit INTEGER NOT NULL,
        word TEXT NOT NULL
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()


def recreate_kindergarten_table():
    conn = sqlite3.connect("vocabulary.db2")
    cursor = conn.cursor()

    # Drop the existing table if it exists
    drop_table_query = "DROP TABLE IF EXISTS kindergarten;"
    cursor.execute(drop_table_query)

    # Create the new kindergarten table
    create_table_query = '''
    CREATE TABLE kindergarten (
        id INTEGER PRIMARY KEY,
        level TEXT NOT NULL,
        title TEXT NOT NULL,
        vocab TEXT NOT NULL
    );
    '''
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()



def enter_vocab_to_database(vocab_words):
    with sqlite3.connect('vocabulary.db2') as conn:
        cursor = conn.cursor()
        insert_query = 'INSERT INTO vocab (book, unit, word) Values (?, ?, ?)'
        cursor.executemany(insert_query, (vocab_words))
        conn.commit()


def enter_kg_vocab_to_database(kg_vocab):
    try:
        with sqlite3.connect('vocabulary.db2') as conn:
            cursor = conn.cursor()
            insert_query = 'INSERT INTO kindergarten (level, title, vocab) Values (?, ?, ?)'
            cursor.executemany(insert_query, kg_vocab)
            conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")



def query_kindergarten_db(level, title):
    with sqlite3.connect("vocabulary.db2") as conn:
        cursor = conn.cursor()
        query = 'SELECT vocab From kindergarten WHERE level=? AND title=?'
        cursor.execute(query, (level, title))
        results = cursor.fetchall()



        conn.commit()
        return results


def remove_duplicates():
    with sqlite3.connect('vocabulary.db2') as conn:
        cursor = conn.cursor()
        delete_query = '''
        DELETE FROM vocab
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM vocab
            GROUP BY book, unit, word
        )
        '''
        cursor.execute(delete_query)
        conn.commit()



def get_vocab(book, unit):
    conn = sqlite3.connect('vocabulary.db2')
    cursor = conn.cursor()

    query = f"SELECT word FROM vocab WHERE book=? AND unit=?"
    cursor.execute(query, (book.capitalize(), unit))

    results = cursor.fetchall()
    if not results:
        return print('Not in Data Base')

    cursor.close()
    conn.close()

    # title = book.capitalize() + ' Unit ' + str(unit) + ' Vocab'
    list1 = []
    for word in results:
        list1.append(''.join(word))

    return list1



def get_kg_vocab(level, title):
    conn = sqlite3.connect('vocabulary.db2')
    cursor = conn.cursor()

    query = 'SELECT vocab From kindergarten WHERE level=? AND title=?'
    cursor.execute(query, (level, title))
    results = cursor.fetchall()

    # Extract vocabulary words from the query results
    vocab_list = [item[0] for item in results]

    print(title + ': ', vocab_list)

    cursor.close()
    conn.commit()
    return vocab_list


def some_function():
    conn = sqlite3.connect('vocabulary.db2')
    cur = conn.cursor()

    # Fetch distinct book names
    cur.execute("SELECT DISTINCT book, unit FROM vocab")
    results = cur.fetchall()

    books_units = {}
    for book, unit in results:
        if book not in books_units:
            books_units[book] = [unit]
        else:
            books_units[book].append(unit)

    conn.close()
    return books_units




def make_kg_dict():
    conn = sqlite3.connect('vocabulary.db2')
    cursor = conn.cursor()

    query = 'SELECT DISTINCT title, vocab FROM kindergarten'
    cursor.execute(query)
    results = cursor.fetchall()

    dict = {}
    for title, vocab in results:
        if title not in dict:
            dict[title] = [vocab]
        else:
            dict[title].append(vocab)


    cursor.close()
    conn.commit()

    return dict


def get_all_books():
    conn = sqlite3.connect('vocabulary.db2')
    cur = conn.cursor()

    # Fetch distinct book names
    cur.execute("SELECT DISTINCT book FROM vocab")
    books = [book[0] for book in cur.fetchall()]
    books.sort()

    conn.close()
    return books


def create_login_db():
    with sqlite3.connect('vocabulary.db2') as conn:
        cur = conn.cursor()
        insertion = '''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        personal_email TEXT NOT NULL UNIQUE,
        bamboozle_email TEXT ,
        bamboozle_password TEXT 
    ); 
        '''
        cur.execute(insertion)
        conn.commit()
        print('db created')
# create_login_db()
def alter_login_db():
    with sqlite3.connect('vocabulary.db2') as conn:
        cur = conn.cursor()

        # Alter the users table to add a new column for the Bamboozle password
        cur.execute('''
        ALTER TABLE users
        ADD COLUMN bamboozle_password TEXT;
        ''')

        conn.commit()

# Call the function to alter the users table

def drop_table():
    with sqlite3.connect('vocabulary.db2') as conn:
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS users;')
        conn.commit()
        print('Dropped')


# drop_table()


from werkzeug.security import generate_password_hash

def add_user(username, password, personal_email, bamboozle_email, bamboozle_password):
    hashed_password = generate_password_hash(password)
    with sqlite3.connect('vocabulary.db2') as conn:
        cur = conn.cursor()
        insert = '''
        INSERT INTO users (username, password, personal_email, bamboozle_email, bamboozle_password)
        VALUES (?, ?, ?, ?, ?)
        '''
        cur.execute(insert, (username, hashed_password, personal_email, bamboozle_email, bamboozle_password))
        conn.commit()
        print('User added successfully.')


def db_connection():
    try:
        conn = psycopg2.connect(host='127.0.0.1', dbname='bamboozle_bot_users', user='postgres', password='1234567890')
        return conn
    except:
        print('No connection')
        return None

def init_db():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL
            
            );
            ''')
            conn.commit()

def show_db():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users')
            users = cur.fetchall()

    for user in users:
        print(user)
def drop_users_table():
    conn = db_connection()
    if conn is not None:
        try:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS users;")
                conn.commit()
                print("Table 'users' dropped successfully.")
        except Exception as e:
            print("An error occurred:", e)
            conn.rollback()
        finally:
            conn.close()
    else:
        print("Connection to the database could not be established.")


# drop_users_table()
# show_db()


if __name__ == '__main__':
    # print(db_connection())
    # init_db()
    pass

    # create_db2()  # Create the database and tables
    # insert_vocab(vocab_entries)  # Insert initial vocabulary entries
    # remove_duplicates()  # Optionally remove duplicates if needed
    # get_vocab('Look1', 11)
    # get_kg_vocab('KG', 'Bedroom')
    # make_kg_dict()
    # insert_vocabs2(vocab_entries2)
    # create_users_db()
    # users_db_connection()



