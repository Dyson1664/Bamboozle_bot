import sqlite3

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


if __name__ == '__main__':
    # create_db2()  # Create the database and tables
    # insert_vocab(vocab_entries)  # Insert initial vocabulary entries
    # remove_duplicates()  # Optionally remove duplicates if needed
    get_vocab('Look1', 11)
    get_kg_vocab('KG', 'Bedroom')
    # make_kg_dict()
    # insert_vocabs2(vocab_entries2)
    # pass




