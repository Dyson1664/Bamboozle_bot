from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from sqlite3 import DatabaseError

import db_5

from docx import Document
from word_search_generator import WordSearch
import threading



from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
from dotenv import load_dotenv
load_dotenv()

PASSWORD = os.getenv('PASSWORD')
EMAIL = os.getenv('EMAIL')
API_KEY = os.getenv('API_KEY')
E_PASS = os.getenv('E_PASS')
E_NAME = os.getenv('E_NAME')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# import openai
# openai.api_key = API_KEY


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


import psycopg2

db_5.create_login_db()


# os.environ["GOOGLE_CHROME_BIN"] = r"C:\Users\PC\Downloads\chrome-win64 (3)\chrome-win64\chrome.exe"

# os.environ["CHROMEDRIVER_PATH"] = r"C:\Users\PC\Downloads\chromedriver-win64 (3)\chromedriver-win64\chromedriver.exe"
from flask_login import UserMixin
from werkzeug.security import check_password_hash
import sqlite3



from cryptography.fernet import Fernet
#run once and made only one time
def generate_key():
    # Generate a key for encryption
    key = Fernet.generate_key()
    # Write the key to a file
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)


def load_key():
    # Load the previously generated key
    return open('secret.key', 'rb').read()

# Load the key
key = load_key()
# Create a Fernet cipher object
cipher_suite = Fernet(key)


@login_manager.user_loader
def load_user(user_id):
    return User.check_user(int(user_id))


class User(UserMixin):
    def __init__(self, id, username, password, personal_email, bamboozle_email, bamboozle_password):
        self.id = id
        self.username = username
        self.password = password
        self.personal_email = personal_email
        self.bamboozle_email = bamboozle_email
        self.bamboozle_password = bamboozle_password

    @staticmethod
    def add_user(username, password, personal_email, bamboozle_email, bamboozle_password):
        # Check if email already exists
        try:
            with sqlite3.connect('vocabulary.db2') as conn:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE personal_email = ?', (personal_email,))
                existing_user = cur.fetchone()

            if existing_user:
                print("User with this email already exists.")
                return None

            hashed_password = generate_password_hash(password)

            if bamboozle_password:
                encrypted_baamboozle_password = cipher_suite.encrypt(bamboozle_password.encode()).decode()
            else:
                encrypted_baamboozle_password = None


            with sqlite3.connect('vocabulary.db2') as conn:
                cur = conn.cursor()
                insert = '''
                INSERT INTO users (username, password, personal_email, bamboozle_email, bamboozle_password)
                VALUES (?, ?, ?, ?, ?)
                '''
                cur.execute(insert, (username, hashed_password, personal_email, bamboozle_email, encrypted_baamboozle_password))
                conn.commit()
                print('User added successfully.')
                return True

        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return None

    @staticmethod
    def check_user(user_id):
        with sqlite3.connect('vocabulary.db2') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cur.fetchone()

        if user:
            if user[5]:
                decrypted_baamboozle_password = cipher_suite.decrypt(user[5].encode()).decode()
            else:
                decrypted_baamboozle_password = None

            user_object = User(
                id=user[0],
                username=user[1],
                password=user[2],
                personal_email=user[3],
                bamboozle_email=user[4],
                bamboozle_password=decrypted_baamboozle_password
            )
            return user_object
        return None

    @staticmethod
    def verify_user(username, password):
        with sqlite3.connect('vocabulary.db2') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cur.fetchone()

        if user and check_password_hash(user[2], password):
            if user[5]:
                decrypted_baamboozle_password = cipher_suite.decrypt(user[5].encode()).decode()
            else:
                decrypted_baamboozle_password = None
            return User(
                id=user[0],
                username=user[1],
                password=user[2],
                personal_email=user[3],
                bamboozle_email=user[4],
                bamboozle_password=decrypted_baamboozle_password
            )
        return None


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys


class Driver:
    def __init__(self):

        # sys.stdout.flush()

        options = Options()
        # Set the binary location to the one provided by the buildpack
        options.binary_location = os.environ.get('GOOGLE_CHROME_SHIM', None)
        if not options.binary_location:
            raise Exception('GOOGLE_CHROME_SHIM not found in environment variables.')

        # Add your desired options
        options.add_argument('--headless=old')  # Use 'new' headless mode for Chrome >= 109
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')

        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', None)
        if not chromedriver_path:
            raise Exception('CHROMEDRIVER_PATH not found in environment variables.')

        chrome_service = Service(executable_path=chromedriver_path)

        print('GOOGLE_CHROME_SHIM:', os.environ.get('GOOGLE_CHROME_SHIM'))
        print('CHROMEDRIVER_PATH:', os.environ.get('CHROMEDRIVER_PATH'))

        self.driver = webdriver.Chrome(service=chrome_service, options=options)

#working
# class Driver:
#     def __init__(self):
#         # chrome_options = webdriver.ChromeOptions()
#         # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
#         # chrome_options.add_argument("--headless")
#         # chrome_options.add_argument('--start-maximized')
#         # chrome_options.add_argument("--disable-dev-shm-usage")
#         # chrome_options.add_argument("--no-sandbox")
#         # self. driver = webdriver.Chrome(options=chrome_options)

#         options = webdriver.ChromeOptions()
#         # https://stackoverflow.com/questions/78996364/chrome-129-headless-shows-blank-window
#         # use old for now because new update has a bug
#         options.add_argument('--headless=old')
#         options.add_argument('--disable-gpu')
#         options.add_argument('--no-sandbox')
#         options.add_argument('--disable-dev-shm-usage')
#         options.add_argument('--window-size=1920,1080')
#         options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
#                              'AppleWebKit/537.36 (KHTML, like Gecko) '
#                              'Chrome/94.0.4606.81 Safari/537.36')
#         options.add_argument('--disable-extensions')
#         options.add_argument('--allow-running-insecure-content')
#         options.add_argument('--ignore-certificate-errors')
#         options.add_argument('--disable-blink-features=AutomationControlled')

#         # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
#         self.driver = webdriver.Chrome(options=options)

    def sign_in(self, url, email, password):
        self.driver.get(url)
        try:
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_input.send_keys(email)
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password")))
            password_input.send_keys(password)
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
            sign_in_button.click()
        except WebDriverException as e:
            print("Exception occurred while interacting with the element: ", e)

    #create game name and description
    def create_game(self, title):
        try:
            title_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'one')))
            title_box.clear()
            title_box.send_keys(title)

            description_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'two')))
            description_box.send_keys(title)

            make_game_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'five')))
            make_game_button.click()

            self.close_pop_up()

        except WebDriverException as e:
            print("Exception occurred while interacting with the element: ", e)

    #loop though adding vocab and clicking pictures
    def create_game_part_two(self, vocabs, email):
        try:
            image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            image_library_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            )
            image_library_button.click()

            image_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "web-lib"))
            )
            image_button.click()
            sleep(6)

            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'close-gif'))
            )
            close_button.click()
            self.accept_cookies()

            for vocab in vocabs:
                if vocab:
                    try:
                        self.questions_search_loop(vocab)
                    except WebDriverException as e:
                        print("Exception occurred while interacting with the element: ", e)

            close_game_button = "//a[@class='btn btn-defaulted']"

            # Use WebDriverWait to wait for the element to be clickable
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, close_game_button))
            ).click()
            # email = user.email
            socketio.emit('email_sent', {'message': f'Bamboozle made for account with email: {email}!'})
            print('Bamboozle made')


        except WebDriverException as e:
            print("Exception occurred while interacting with the element: ", e)

    def questions_search_loop(self, vocabs):
        input_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "problem"))
        )
        input_box.click()
        input_box.clear()
        input_box.send_keys('What is it?')

        vocab_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "solution1"))
        )
        vocab_box.click()
        vocab_box.clear()
        vocab_box.send_keys(vocabs)


        image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
        ).click()

        try:
            first_image = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(1) img.giphy-gif-img.giphy-img-loaded"))
            )
            first_image.click()

        except Exception as e:
            try:
                fifth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded"))
                )
                fifth_image.click()

            except Exception as e:
                print('close/re-open')
                self.close_reopen()
                print('Couldn\'t click first pic. Had to close and reopen', e)

            print('Could not click first image')

        save_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tally"))
        )
        save_button.click()


    def close_reopen(self):
        try:
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'close-gif'))
            )
            close_button.click()


            image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            ).click()

            try:
                sixth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(6) img.giphy-gif-img.giphy-img-loaded"))
                )
                sixth_image.click()

            except Exception as e:
                fifth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded"))
                )
                fifth_image.click()

                print('Could not even click 5th image', e)

        except WebDriverException as e:
            print("Exception occurred while closing the popup: ", e)

    def accept_cookies(self):
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".js-cookie-consent-agree.cookie-consent__agree.btn.btn-primaryed"))
            )
            cookie_button.click()
            print('Cookies closed')


            # close_gpt = WebDriverWait(self.driver, 5).until(
            #     EC.element_to_be_clickable(
            #         (By.XPATH, "//*[@id=\"beamerAnnouncementBar\"]/div[2]/div[2]")
            #     )
            # )
            # close_gpt.click()

        except Exception as e:
            print('Could not click the cookie button', e)

    def close_pop_up(self):
        try:
            pop_up_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@id=\'beamerAnnouncementSnippet\']')
                )
            ).click()
        except Exception as e:
            print('Could not click pop up button', e)


    def create_bamboozle(self, url, email, password, title, vocabs):
        self.sign_in(url, email, password)
        self.create_game(title)
        self.create_game_part_two(vocabs, email)

    def create_quiz(self, vocab_words, email):
        quiz_variable = 'Review Quiz'
        prompt = create_prompt(vocab_words)
        response = generate_esl_quiz(prompt, max_tokens=550)
        word_s = create_a_word_document(response)
        send_email_with_attachment(email, word_s, quiz_variable)


    def create_word_search(self, vocabs, email):
        wordsearch_variable = 'Wordsearch'
        wordsearch_path = make_word_search(vocabs)
        send_email_with_attachment(email, wordsearch_path, wordsearch_variable)

    def close(self):
        self.driver.quit()

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.verify_user(username, password)

        if user:
            login_user(user)
            flash('You are now logged in', 'success')
            return redirect(url_for('book_unit'))
        else:
            flash('Invalid credentials. Please try again or register.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        personal_email = request.form.get('personal_email')
        bamboozle_email = request.form.get('bamboozle_email') or None
        bamboozle_password = request.form.get('bamboozle_password') or None

        if username and password and personal_email:
            user_created = User.add_user(username, password, personal_email, bamboozle_email, bamboozle_password)
            if user_created:
                flash('Registration successful!', 'success')
                return redirect(url_for('login'))
            else:
                flash('User with this email already exists.', 'danger')
                return redirect(url_for('register'))

        else:
            flash('Username, password and personal email are required.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have just logged out', 'success')
    return redirect(url_for('login'))


# main webpag
@app.route('/', methods=['GET', 'POST'])
@login_required
def book_unit():
    email = current_user.personal_email
    bamboozle_email = current_user.bamboozle_email
    bamboozle_password = current_user.bamboozle_password
    selected_book, selected_unit, combined_vocab = setup_bookunit()
    try:
        book_to_units, books, kg_vocab = setup_function()

    except DatabaseError as e:
        print(f"Database error: {e}")
        return render_template('error.html', error_message="Database error occurred.")


    if request.method == 'POST':
        selected_book = request.form.get('bookName', 'None')
        selected_unit = request.form.get('unitNumber', 'None')
        session['selected_book'] = selected_book
        session['selected_unit'] = selected_unit

        if request.form['action'] == 'bamboozle':
            print('1')
            vocab_words = request.form.get('vocab', '')
            if vocab_words:
                print('2')
                print(vocab_words)
                print(type(vocab_words))
                flash('Creating Bamboozle', 'info')
                # vocabs = vocab_words.split(', ') if vocab_words else []

            title = request.form.get('bamboozleTitle', '')
            print('3')
            return handle_bamboozle(vocab_words, title, books, book_to_units, kg_vocab, selected_book, selected_unit, bamboozle_email, bamboozle_password)

        elif request.form['action'] == 'reviewQuiz':
            vocabs = request.form.get('vocab', '')
            if vocabs:
                flash('Creating Review Quiz', 'info')

            return handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email)

        elif request.form['action'] == 'ShowVocab':

            book = request.form.get('bookName', 'None')
            unit = request.form.get('unitNumber', 'None')
            kg_category = request.form.get('kgTitle', 'KG')
            existing_vocab = request.form.get('vocab', '')
            new_combined_vocab = []
            # Reset selected_book and selected_unit to 'None' after processing ShowVocab
            session['selected_book'] = 'None'
            selected_book = 'None'

            # Fetch vocab for selected book and unit
            if book != 'None':
                new_vocab = db_5.get_vocab(book, unit)

                new_combined_vocab.extend(new_vocab)

            # Fetch vocab for selected kindergarten category

            if kg_category != 'NONE':
                kg_vocab_list = kg_vocab.get(kg_category, [])

                new_combined_vocab.extend(kg_vocab_list)

            # Append new vocab to existing vocab

            if existing_vocab:

                combined_vocab = ', '.join(filter(None, [existing_vocab, ', '.join(new_combined_vocab)]))

            else:

                # combined_vocab = ', '.join(new_combined_vocab)
                combined_vocab = ', '.join(str(item) for item in new_combined_vocab)


            return render_template('book_unit.html', vocab=combined_vocab, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)


        elif request.form['action'] == "wordSearch":
            print(f"Flash messages: {session.get('_flashes', [])}")

            vocabs = request.form.get('vocab')
            # remove spacing for wordsearch to work properly
            compress_vocab = vocabs.replace(' ', '')
            if compress_vocab:
                flash('Creating Word Search!', 'info')

                return handle_wordsearch(vocabs=compress_vocab, normal_vocabs=vocabs, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit, email=email)


    return render_template('book_unit.html', vocab=combined_vocab, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)

#query database for book and coresponding unit vocab
def setup_function():
    book_to_units = db_5.some_function()
    books = db_5.get_all_books()
    kg_vocab = db_5.make_kg_dict()
    return book_to_units, books, kg_vocab


# Retrieves and initializes session variables for selected book, unit,
# and combined vocabulary, used in the book unit route.
def setup_bookunit():
    if 'selected_book' not in session or request.method == 'GET':
        session['selected_book'] = 'None'
    if 'selected_unit' not in session or request.method == 'GET':
        session['selected_unit'] = 'None'

    selected_book = session.get('selected_book', 'None')
    selected_unit = session.get('selected_unit', 'None')
    combined_vocab = ''
    return selected_book, selected_unit, combined_vocab



def handle_bamboozle(vocab_words, bamboozle_title, books, book_to_units, kg_vocab, selected_book, selected_unit, bamboozle_email, bamboozle_password):
    if not vocab_words:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)
    # Split vocab words into a list
    vocabs = vocab_words.split(', ')
    print('split:', vocabs)

    def run_bamboozle(driver, url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs):
        try:
            if bamboozle_email and bamboozle_password:
                driver.create_bamboozle(url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs)
            else:
                flash('Baamboozle credentials are missing. Please update your profile.', 'danger')
        except Exception as e:
            print(e)
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        thread = threading.Thread(target=run_bamboozle,
                                  args=(driver, url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs))
        thread.start()

    # Return the template with the updated vocabulary
    return render_template('book_unit.html',  vocab=vocab_words, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)

def handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email):
    if not vocabs:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, kg_vocab=kg_vocab,
                               book_to_units=book_to_units, selected_book=selected_book, selected_unit=selected_unit)

    def create_review_quiz(driver, vocabs, email):
        print(f'Vocabs**********: {vocabs}, email: {email}')
        try:
            driver.create_quiz(vocabs, email)
        except Exception as e:
            print(e)
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        quiz_thread = threading.Thread(target=create_review_quiz, args=(driver, vocabs, email))
        quiz_thread.start()


    return render_template('book_unit.html', vocab=vocabs, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab,
                           selected_book=selected_book, selected_unit=selected_unit)


def handle_wordsearch(vocabs, normal_vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email):
    if not vocabs:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, kg_vocab=kg_vocab,
                               book_to_units=book_to_units,
                               selected_book=selected_book, selected_unit=selected_unit)

    def run_word_search(driver, vocabs, email):
        print(f'Vocabs*******: {vocabs}')
        try:
            driver.create_word_search(vocabs, email)
        except Exception as e:
            print(e)

        finally:
            driver.close()


    if vocabs:
        driver = Driver()
        word_search_thread = threading.Thread(target=run_word_search, args=(driver, vocabs, email))
        word_search_thread.start()


    return render_template('book_unit.html', vocab=normal_vocabs, books=books, kg_vocab=kg_vocab, book_to_units=book_to_units,
                           selected_book=selected_book, selected_unit=selected_unit)




url = 'https://www.baamboozle.com/games/create'


def create_prompt(vocabs):
    return f"""Hello, I need your assistance to create an EASY and I really mean Easy ESL quiz for ten-year-old students using the following vocabulary words: {vocabs}. The quiz should be straightforward, engaging, and designed for beginners. Here's the format I'd like you to follow:

1. **Fill in the Blanks:** 
   - Develop TEN sentences with a blank space for a word from the vocabulary list. 
   - Each sentence should use a different vocabulary word in a context that helps infer its meaning.
   - Ensure the sentences are simple, age-appropriate, and provide enough context clues to guess the missing word.
   - List the vocabulary words at the top of this section for easy reference.

2. **Reading Comprehension:**
   - Write a short, engaging story appropriate for the age group, incorporating some of the vocabulary words.
   - After the story, include FIVE comprehension questions that test the students' understanding of the text and how the vocabulary words are used within it.
   - The story and questions should be simple enough for students at this level to understand without external help.

Please do not include the answers in the quiz. Aim to keep the total length of the quiz to about one page. For clarity, here's a structure outline for your reference:

**Vocabulary Words:** 
{vocabs}

**Fill in the Blanks:**
1. Sentence with a blank using vocab1.
2. Sentence with a blank using vocab2.
... and so on.

**Reading Comprehension:**
[Short story incorporating some of the vocabulary words]

**Comprehension Questions:**
1. Question about the story.
2. Another question about the story.
... and so on."""



def generate_esl_quiz(prompt, max_tokens=550):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a skilled ESL teacher."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {e}"

def make_word_search(vocab):
    print(vocab)
    puzzle = WordSearch(vocab)
    puzzle.show()
    filename = 'word_search.pdf'
    puzzle.save(filename)
    wordsearch_path = os.path.abspath(filename)

    # location = puzzle.save(path=r"C:\Users\PC\Desktop\work_webpage\Bamboozle_ESL-game\word_search.pdf")
    return wordsearch_path


def create_a_word_document(text):
    doc = Document()
    doc.add_paragraph(text)
    filename = 'word_doc.docx'
    doc.save(filename)
    path = os.path.abspath(filename)
    return path

from flask_socketio import SocketIO

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Production settings
    async_mode = 'gevent'
else:
    # Development settings
    async_mode = 'threading'

socketio = SocketIO(app, async_mode=async_mode)

@socketio.on('connect')
def handle_connection():
    print('Client connected')



import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
from flask_socketio import SocketIO, emit
import mimetypes
import shutil


def send_email_with_attachment(to_email, path, content, file_path=None):

    # Your Gmail account credentials from environment variables
    from_email = os.getenv('E_NAME')  # Your Gmail email (from .env)
    password = os.getenv('E_PASS')  # Your Gmail App Password (from .env)

    # Create the email message object
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = f"Here is your {content} :)"  # Set subject based on the content type

    # Attach the body content to the email (plain text)
    body_content = f"Please find the attached {content}."
    msg.attach(MIMEText(body_content, 'plain'))

    # Use the provided path to the file
    file_path = path if path else file_path

    # Attach a file if the path is provided
    if file_path:
        try:
            # Detect MIME type based on file extension
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'  # Default for binary files

            # Open the file and attach it
            with open(file_path, "rb") as attachment:
                part = MIMEBase(*mime_type.split("/"))
                part.set_payload(attachment.read())

            # Encode the file payload in base64
            encoders.encode_base64(part)

            # Add header to the attachment
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(file_path)}"'
            )

            # Attach the file to the email
            msg.attach(part)

        except Exception as e:
            print(f'Failed to attach file: {e}')
            socketio.emit('email_error', {'message': f'Failed to attach file: {str(e)}'})

    try:
        # Set up the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection

        # Login to the Gmail account
        server.login(from_email, password)

        # Send the email
        server.sendmail(from_email, to_email, msg.as_string())

        # If email sent successfully, emit a WebSocket event
        socketio.emit('email_sent', {'message': f'{content} sent successfully to {to_email}'})
        print(f'Email sent successfully to {to_email}')

    except Exception as e:
        # Emit a WebSocket event in case of failure
        socketio.emit('email_error', {'message': f'Failed to send email to {to_email}. Error: {str(e)}'})
        print(f'Failed to send email: {e}')

    finally:
        # Close the connection to the server
        server.quit()

        # Ensure the file gets deleted after sending the email
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f'{file_path} deleted successfully.')
            except Exception as e:
                print(f'Error deleting file: {e}')




if __name__ == '__main__':
    # socketio.run(app, debug=True, port=5001, use_reloader=False, allow_unsafe_werkzeug=True)
    socketio.run(app, debug=True)
    # pass
#finished :)



