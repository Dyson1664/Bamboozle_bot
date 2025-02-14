from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from time import sleep
import logging
import sys
import psycopg2

# import db_5
import postgres_db

from docx import Document
from word_search_generator import WordSearch
import threading
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

 # = db_5
load_dotenv()

PASSWORD = os.getenv('PASSWORD')
EMAIL = os.getenv('EMAIL')
API_KEY = os.getenv('API_KEY')
E_PASS = os.getenv('E_PASS')
E_NAME = os.getenv('E_NAME')


from flask import Flask, request
from flask_login import current_user
from flask_socketio import SocketIO
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Production settings
    async_mode = 'gevent'
    debug = True
else:
    # Development settings
    async_mode = 'threading'
    debug = False

socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins='*')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE_URL = os.getenv('DATABASE_URL')

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s: %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')
# logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from psycopg2 import DatabaseError
from cryptography.fernet import Fernet


def load_key():
    key = os.getenv('FERNET_KEY')
    if key is None:
        raise ValueError("No FERNET_KEY found in environment variables")
    return key.encode()

key = load_key()
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
            conn = get_db_connection()
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE personal_email = %s', (personal_email,))
            existing_user = cur.fetchone()

            if existing_user:
                print("User with this email already exists.")
                return None

            hashed_password = generate_password_hash(password)

            if bamboozle_password:
                encrypted_bamboozle_password = cipher_suite.encrypt(bamboozle_password.encode()).decode()
            else:
                encrypted_bamboozle_password = None

            insert_query = '''
                        INSERT INTO users (username, password, personal_email, bamboozle_email, bamboozle_password)
                        VALUES (%s, %s, %s, %s, %s)
                        '''
            cur.execute(insert_query,
                        (username, hashed_password, personal_email, bamboozle_email, encrypted_bamboozle_password))
            conn.commit()
            print('User added successfully.')
            return True

        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            if conn:
                cur.close()
                conn.close()

    @staticmethod
    def check_user(user_id):
        try:
            conn = get_db_connection()
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user = cur.fetchone()

            if user:
                decrypted_bamboozle_password = cipher_suite.decrypt(user[5].encode()).decode() if user[5] else None
                user_object = User(
                    id=user[0],
                    username=user[1],
                    password=user[2],
                    personal_email=user[3],
                    bamboozle_email=user[4],
                    bamboozle_password=decrypted_bamboozle_password
                )
                return user_object
            return None

        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            if conn:
                cur.close()
                conn.close()


    @staticmethod
    def verify_user(username, password):
        try:
            conn = get_db_connection()
            if conn is None:
                return None
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cur.fetchone()

            if user and check_password_hash(user[2], password):
                decrypted_bamboozle_password = cipher_suite.decrypt(user[5].encode()).decode() if user[5] else None
                return User(
                    id=user[0],
                    username=user[1],
                    password=user[2],
                    personal_email=user[3],
                    bamboozle_email=user[4],
                    bamboozle_password=decrypted_bamboozle_password
                )
            return None

        except psycopg2.Error as e:
            print(f"An error occurred: {e}")
            return None

        finally:
            if conn:
                cur.close()
                conn.close()


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys
import tempfile

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')


import logging
logging.getLogger('selenium').setLevel(logging.WARNING)


class Driver:
    def __init__(self):
        options = Options()

        # Include all the same arguments you mentioned:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36')

        # Force a unique user-data-dir for each session:
        temp_user_dir = tempfile.mkdtemp()
        options.add_argument(f'--user-data-dir={temp_user_dir}')

        if ENVIRONMENT == 'production':
            service = Service("chromedriver")   # Use chromedriver from PATH
            # No binary_location here -- let PATH find 'chrome'.
        else:
            local_chrome_bin = os.getenv('GOOGLE_CHROME_BIN_LOCAL')
            local_driver_path = os.getenv('CHROMEDRIVER_PATH_LOCAL')

            if local_chrome_bin:
                options.binary_location = local_chrome_bin

            if local_driver_path:
                service = Service(executable_path=local_driver_path)
            else:
                # If you just have chromedriver in your PATH on Windows or Mac:
                service = Service("chromedriver")

        # Create webdriver:
        self.driver = webdriver.Chrome(service=service, options=options)


    def sign_in(self, url, email, password):
        print('1')
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

            self.accept_cookies()

            make_game_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'five')))
            make_game_button.click()

            sleep(2)

            image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            ).click()
            sleep(1)


            set_to_image_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "web-lib"))
            )
            set_to_image_button.click()
            sleep(1)

            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.close.close-gif"))
            )
            close_button.click()
            sleep(2)




        except WebDriverException as e:
            print("Exception occurred while interacting with the element: ", e)

    #loop though adding vocab and clicking pictures
    def create_game_part_two(self, vocabs, email):
        try:
            # image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            # image_library_button = WebDriverWait(self.driver, 20).until(
            #     EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            # )
            # image_library_button.click()
            #
            # image_button = WebDriverWait(self.driver, 20).until(
            #     EC.element_to_be_clickable((By.ID, "web-lib"))
            # )
            # image_button.click()
            # sleep(6)
            #
            # close_button = WebDriverWait(self.driver, 10).until(
            #     EC.element_to_be_clickable((By.CLASS_NAME, 'close-gif'))
            # )
            # close_button.click()
            self.accept_cookies()

            for vocab in vocabs:
                if vocab:
                    try:
                        print(f'Creating: {vocab}')
                        self.questions_search_loop(vocab)
                    except WebDriverException as e:
                        print("Exception occurred while interacting with the element: ", e)

            close_game_button = "//a[@class='btn btn-defaulted']"

            # Use WebDriverWait to wait for the element to be clickable
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, close_game_button))
            ).click()
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
        sleep(1)


        image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
        ).click()
        sleep(1)

        try:
            first_image = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(1) img.giphy-gif-img.giphy-img-loaded"))
            )
            first_image.click()
            print('first image clicked')

        except Exception as e:
            try:
                fifth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded"))
                )
                fifth_image.click()
                print('fifth image clicked after first image not able to. Didnt close reopen')

            except Exception as e:
                print('calling close/re-open')
                sleep(1)
                self.close_reopen()
                sleep(2)






        save_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tally"))
        )
        save_button.click()


    def close_reopen(self):
        try:
            print('trying to close reopen')
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
                print('clicked 6th image')

            except Exception as e:
                fifth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded"))
                )
                fifth_image.click()

                print('clicked 6th image', e)

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

    def create_quiz(self, vocab_words, email, user_id):
        quiz_variable = 'Review Quiz'
        prompt = create_prompt(vocab_words)
        response = generate_esl_quiz(prompt, max_tokens=550)
        word_s = create_a_word_document(response)
        send_email_with_attachment(email, word_s, quiz_variable, user_id)


    def create_word_search(self, vocabs, email, user_id):
        wordsearch_variable = 'Wordsearch'
        wordsearch_path = make_word_search(vocabs)
        send_email_with_attachment(email, wordsearch_path, wordsearch_variable, user_id)

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
import time
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from psycopg2 import DatabaseError
import postgres_db



# A simple global cache variable (in production, consider using a more robust solution)
global_data_cache = None
cache_last_updated = None

def get_cached_setup_data(force_refresh=False):
    global global_data_cache, cache_last_updated
    # Refresh cache every 5 minutes (300 seconds) or if forced
    if force_refresh or global_data_cache is None or (cache_last_updated is None or (time.time() - cache_last_updated > 300)):
        # Call your combined setup function from postgres_db
        global_data_cache = postgres_db.setup_function_combined()
        cache_last_updated = time.time()
    return global_data_cache


@app.route('/', methods=['GET', 'POST'])
@login_required
def book_unit():
    total_start = time.time()
    print("book_unit: start")

    # Retrieve user info
    email = current_user.personal_email
    bamboozle_email = current_user.bamboozle_email
    bamboozle_password = current_user.bamboozle_password

    # Setup session variables for book/unit
    selected_book, selected_unit, combined_vocab = setup_bookunit()
    print(f"setup_bookunit took: {time.time() - total_start:.3f} seconds")

    # Setup other data from the database (using cache)
    try:
        t_setup_function_start = time.time()
        book_to_units, books, kg_vocab = get_cached_setup_data()
        t_setup_function_end = time.time()
        print(f"get_cached_setup_data took: {t_setup_function_end - t_setup_function_start:.3f} seconds")
    except DatabaseError as e:
        print(f"Database error: {e}")
        return render_template('error.html', error_message="Database error occurred.")


    if request.method == 'POST':
        t_post_start = time.time()
        selected_book = request.form.get('bookName', 'None')
        selected_unit = request.form.get('unitNumber', 'None')
        session['selected_book'] = selected_book
        session['selected_unit'] = selected_unit
        print(f"Session update took: {time.time() - t_post_start:.3f} seconds")

        action = request.form['action']
        if action == 'bamboozle':
            t_bamboozle_start = time.time()
            vocab_words = request.form.get('vocab', '')
            if vocab_words:
                flash('Creating Bamboozle', 'info')
            title = request.form.get('bamboozleTitle', '')
            result = handle_bamboozle(vocab_words, title, books, book_to_units, kg_vocab, selected_book, selected_unit, bamboozle_email, bamboozle_password)
            print(f"handle_bamboozle took: {time.time() - t_bamboozle_start:.3f} seconds")
            return result

        elif action == 'reviewQuiz':
            t_review_quiz_start = time.time()
            vocabs = request.form.get('vocab', '')
            if vocabs:
                flash('Creating Review Quiz', 'info')
            result = handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email)
            print(f"handle_review_quiz took: {time.time() - t_review_quiz_start:.3f} seconds")
            return result

        elif action == 'ShowVocab':
            t_show_vocab_start = time.time()
            book = request.form.get('bookName', 'None')
            unit = request.form.get('unitNumber', 'None')
            kg_category = request.form.get('kgTitle', 'KG')
            existing_vocab = request.form.get('vocab', '')
            new_combined_vocab = []
            # Reset selected_book to 'None'
            session['selected_book'] = 'None'
            selected_book = 'None'

            # Fetch vocab for selected book and unit
            if book != 'None':
                new_vocab = postgres_db.get_vocab(book, unit)
                new_combined_vocab.extend(new_vocab)

            # Fetch vocab for selected kindergarten category
            if kg_category != 'NONE':
                kg_vocab_list = kg_vocab.get(kg_category, [])
                new_combined_vocab.extend(kg_vocab_list)

            # Merge with any existing vocab
            if existing_vocab:
                combined_vocab = ', '.join(filter(None, [existing_vocab, ', '.join(new_combined_vocab)]))
            else:
                combined_vocab = ', '.join(str(item) for item in new_combined_vocab)
            print(f"handle ShowVocab took: {time.time() - t_show_vocab_start:.3f} seconds")
            return render_template('book_unit.html', vocab=combined_vocab, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)

        elif action == "wordSearch":
            t_word_search_start = time.time()
            print(f"Flash messages: {session.get('_flashes', [])}")
            vocabs = request.form.get('vocab')
            compress_vocab = vocabs.replace(' ', '')
            if compress_vocab:
                flash('Creating Word Search!', 'info')
                result = handle_wordsearch(vocabs=compress_vocab, normal_vocabs=vocabs, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit, email=email)
                print(f"handle_wordsearch took: {time.time() - t_word_search_start:.3f} seconds")
                return result

    total_end = time.time()
    print(f"Total time in book_unit route: {total_end - total_start:.3f} seconds")
    return render_template('book_unit.html', vocab=combined_vocab, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)


# Retrieves and initializes session variables for selected book, unit,
# and combined vocabulary, used in the book unit route.
def setup_bookunit():
    t_setup_start = time.time()
    if 'selected_book' not in session or request.method == 'GET':
        session['selected_book'] = 'None'
    if 'selected_unit' not in session or request.method == 'GET':
        session['selected_unit'] = 'None'
    selected_book = session.get('selected_book', 'None')
    selected_unit = session.get('selected_unit', 'None')
    combined_vocab = ''
    print(f"setup_bookunit took: {time.time() - t_setup_start:.3f} seconds")
    return selected_book, selected_unit, combined_vocab






def handle_bamboozle(vocab_words, bamboozle_title, books, book_to_units, kg_vocab, selected_book, selected_unit, bamboozle_email, bamboozle_password):
    if not vocab_words:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)
    # Split vocab words into a list
    vocabs = vocab_words.split(', ')
    def run_bamboozle(driver, url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs, user_id):
        try:
            if bamboozle_email and bamboozle_password:
                driver.create_bamboozle(url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs)
                sid = user_sid_map.get(str(user_id))
                if sid:
                    socketio.emit('email_sent', {'message': f'Bamboozle game created successfully!'}, room=sid)
                else:
                    print(f'No sid found for user {user_id}')
            else:
                flash('Baamboozle credentials are missing. Please update your profile.', 'danger')
        except Exception as e:
            print(e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error', {'message': f'Failed to create Bamboozle game. Error: {str(e)}'}, room=sid)
            else:
                print(f'No sid found for user {user_id}')
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        user_id = current_user.get_id()
        socketio.start_background_task(run_bamboozle, driver, url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs, user_id)

    # Return the template with the updated vocabulary
    return render_template('book_unit.html', vocab=vocab_words, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)

def handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email):
    if not vocabs:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, kg_vocab=kg_vocab,
                               book_to_units=book_to_units, selected_book=selected_book, selected_unit=selected_unit)

    def create_review_quiz(driver, vocabs, email, user_id):
        try:
            driver.create_quiz(vocabs, email, user_id)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_sent', {'message': f'Review Quiz sent successfully to {email}'}, room=sid)
            else:
                print(f'No sid found for user {user_id}')
        except Exception as e:
            print(e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error', {'message': f'Failed to send Review Quiz to {email}. Error: {str(e)}'}, room=sid)
            else:
                print(f'No sid found for user {user_id}')
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        user_id = current_user.get_id()
        socketio.start_background_task(create_review_quiz, driver, vocabs, email, user_id)

    return render_template('book_unit.html', vocab=vocabs, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab,
                           selected_book=selected_book, selected_unit=selected_unit)
def handle_wordsearch(vocabs, normal_vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email):
    if not vocabs:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, kg_vocab=kg_vocab,
                               book_to_units=book_to_units,
                               selected_book=selected_book, selected_unit=selected_unit)

    def run_word_search(driver, vocabs, email, user_id):
        try:
            driver.create_word_search(vocabs, email, user_id)
            # Get the client's sid
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_sent', {'message': f'Wordsearch sent successfully to {email}'}, room=sid)
            else:
                print(f'No sid found for user {user_id}')
        except Exception as e:
            print(e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error', {'message': f'Failed to send wordsearch to {email}. Error: {str(e)}'}, room=sid)
            else:
                print(f'No sid found for user {user_id}')
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        user_id = current_user.get_id()
        socketio.start_background_task(run_word_search, driver, vocabs, email, user_id)

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
        import openai
        openai.api_key = os.getenv("API_KEY")  # read from environment
        response = openai.ChatCompletion.create(
            model="gpt-4",
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

user_sid_map = {}

@socketio.on('register')
def handle_register(data):
    user_id = data.get('user_id')
    sid = request.sid
    if user_id:
        user_sid_map[user_id] = sid
        print(f'User {user_id} registered with sid {sid}')


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    # Remove the sid from the user_sid_map
    user_id = None
    for uid, user_sid in user_sid_map.items():
        if user_sid == sid:
            user_id = uid
            break
    if user_id:
        user_sid_map.pop(user_id, None)
        print(f'User {user_id} disconnected')


@socketio.on('connect')
def handle_connection():
    print('Client connected')

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
import mimetypes


def send_email_with_attachment(to_email, path, content, user_id, file_path=None):
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
        sid = user_sid_map.get(str(user_id))
        if sid:
            socketio.emit('email_sent', {'message': f'{content} sent successfully to {to_email}'}, room=sid)
        else:
            print(f'No sid found for user {user_id}')
        print(f'Email sent successfully to {to_email}')

    except Exception as e:
        # Emit a WebSocket event in case of failure
        sid = user_sid_map.get(str(user_id))
        if sid:
            socketio.emit('email_error', {'message': f'Failed to send {content} to {to_email}. Error: {str(e)}'},
                          room=sid)
        else:
            print(f'No sid found for user {user_id}')
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
    socketio.run(app, debug=debug)
    pass



