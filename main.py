from xml.sax.saxutils import escape

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import time
from time import sleep
import logging
import sys
import psycopg2
import tempfile

import postgres_db
from docx import Document
from word_search_generator import WordSearch
import threading
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import mimetypes

PASSWORD = os.getenv('PASSWORD')
EMAIL = os.getenv('EMAIL')
API_KEY = os.getenv('API_KEY')
E_PASS = os.getenv('E_PASS')
E_NAME = os.getenv('E_NAME')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    # Production settings
    async_mode = 'gevent'
    debug = False
else:
    # Development settings
    async_mode = 'threading'
    debug = True

from flask_socketio import SocketIO

socketio = SocketIO(app, async_mode=async_mode, cors_allowed_origins='*')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE_URL = os.getenv('DATABASE_URL')
from psycopg2 import DatabaseError


def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None


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
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
        )

        # Force a unique user-data-dir for each session:
        temp_user_dir = tempfile.mkdtemp()
        options.add_argument(f'--user-data-dir={temp_user_dir}')

        if ENVIRONMENT == 'production':
            service = Service("chromedriver")  # Use chromedriver from PATH
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
        try:
            self.driver.get(url)
            email_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_input.send_keys(email)
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_input.send_keys(password)
            sign_in_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
            )
            sign_in_button.click()

        # Catch broad Selenium errors or any other exception
        except (WebDriverException, Exception) as e:
            print("Exception occurred in sign_in:", e)

    # create game name and description
    def create_game(self, title):
        try:
            print('Creating game function called')
            title_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'one'))
            )
            title_box.clear()
            title_box.send_keys(title)
            print('Title game entered')

            description_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'two'))
            )
            description_box.send_keys(title)
            print('description_box entered')

            self.accept_cookies()

            make_game_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'five'))
            )
            make_game_button.click()
            print('Make game clicked')
            sleep(2)

            # Open image library
            image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            ).click()
            sleep(1)

            # Switch to the standard image library
            set_to_image_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "web-lib"))
            )
            set_to_image_button.click()
            sleep(1)

            # Close library
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.close.close-gif"))
            )
            close_button.click()
            sleep(2)
            print('Image opened and closed')

        except (WebDriverException, Exception) as e:
            print("Exception occurred in create_game:", e)

    # loop though adding vocab and clicking pictures
    def create_game_part_two(self, vocabs, email):
        """Add vocab Q&A pairs and attempt to attach images."""
        try:
            self.accept_cookies()
            for vocab in vocabs:
                if vocab:
                    try:
                        print(f'Creating: {vocab}')
                        self.questions_search_loop(vocab)
                    except (WebDriverException, Exception) as e:
                        print("create_game_part_two - error in questions_search_loop:", e)

            close_game_button = "//a[@class='btn btn-defaulted']"
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, close_game_button))
            ).click()
            print('Bamboozle made')

        except (WebDriverException, Exception) as e:
            print("Exception in create_game_part_two:", e)

    def questions_search_loop(self, vocab):
        """Attempt to fill in the question, answer, open library, and click an image."""
        print(f'starting questions_search_loop for {vocab}')
        try:
            sleep(2)
            input_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "problem"))
            )
            input_box.clear()
            print('Input box cleared')

            input_box.send_keys('What is it?')
            print('Input box entered What is it?')



            vocab_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "solution1"))
            )
            vocab_box.clear()
            vocab_box.send_keys(vocab)
            sleep(1)
            print(f'Input box entered {vocab}')


            # Try up to 3 attempts at picking an image
            for attempt in range(3):
                print(f"--- Attempt {attempt + 1} ---")
                try:
                    # 1) Open image library
                    image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
                    WebDriverWait(self.driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
                    ).click()

                    # 2) Wait for images to load
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "div.giphy-gif img.giphy-gif-img.giphy-img-loaded")
                        )
                    )

                    # 3) Try the first image
                    try:
                        first_image = WebDriverWait(self.driver, 15).until(
                            EC.element_to_be_clickable(
                                (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(1) img.giphy-gif-img.giphy-img-loaded")
                            )
                        )
                        first_image.click()
                        break  # success
                    except Exception as e_first:
                        print(f"Failed to click FIRST image of {vocab}. Error: {e_first}")
                        # 4) Try the fifth image
                        try:
                            fifth_image = WebDriverWait(self.driver, 15).until(
                                EC.element_to_be_clickable(
                                    (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded")
                                )
                            )
                            fifth_image.click()
                            print(f"Clicked FIFTH image of {vocab} successfully.")
                            break  # success
                        except Exception as e_fifth:
                            print(f"Failed to click FIFTH image of {vocab}. Error: {e_fifth}")
                            print("Both first & fifth failed, calling close_reopen()...")

                            if self.close_reopen(vocab):
                                print("close_reopen() succeeded, breaking out of loop.")
                                break
                            else:
                                print("close_reopen() failed too.")
                                if attempt < 2:
                                    sleep(2)
                                    continue
                                else:
                                    print("No more attempts left.")
                                    break

                except Exception as e_outer:
                    print(f"Exception opening library or waiting for images for {vocab}: {e_outer}")

                    if self.close_reopen(vocab):
                        print("close_reopen() succeeded, breaking out of loop.")
                        break
                    else:
                        if attempt < 2:
                            sleep(2)
                            continue
                        else:
                            break

            # Finally, click 'Save'
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "tally"))
            )
            save_button.click()

        except (WebDriverException, Exception) as e:
            print(f"questions_search_loop general exception for {vocab}:", e)

    def close_reopen(self, vocab):
        """
        Close the popup, re-open, and attempt to click the 6th image;
        if that fails, try the 5th. Return True if successful, False otherwise.
        """
        try:
            print('trying to close reopen')
            close_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'close-gif'))
            )
            close_button.click()

            # Re-open the image library
            image_library_button_xpath = "//div[@id='question-form']//button[@type='button']"
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, image_library_button_xpath))
            ).click()

            # Attempt the 6th image first
            try:
                sixth_image = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(6) img.giphy-gif-img.giphy-img-loaded")
                    )
                )
                sixth_image.click()
                print(f'clicked 6th image of {vocab} in close_reopen')
                return True

            except Exception as e_sixth:
                print(f"Could not click the 6th image of {vocab}: {e_sixth}")
                print("Trying the 5th image instead...")

                try:
                    fifth_image = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.giphy-gif:nth-of-type(5) img.giphy-gif-img.giphy-img-loaded")
                        )
                    )
                    fifth_image.click()
                    print(f'clicked 5th image of {vocab} in close_reopen')
                    return True

                except Exception as e_fifth:
                    print(f"Could not click the 5th image: {e_fifth}")
                    return False  # Both 6th and 5th failed

        except (WebDriverException, Exception) as e:
            print("Exception occurred while closing popup or re-opening:", e)
            return False

    def accept_cookies(self):
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".js-cookie-consent-agree.cookie-consent__agree.btn.btn-primaryed"))
            )
            cookie_button.click()
            print('Cookies closed')

        except Exception as e:
            print('Could not click the cookie button', e)

    def close_pop_up(self):
        try:
            pop_up_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@id=\'beamerAnnouncementSnippet\']'))
            )
            pop_up_button.click()
        except Exception as e:
            print('Could not click pop up button', e)

    def create_bamboozle(self, url, email, password, title, vocabs):
        """Encapsulates entire Bamboozle creation flow."""
        try:
            self.sign_in(url, email, password)
            self.create_game(title)
            self.create_game_part_two(vocabs, email)
        except (WebDriverException, Exception) as e:
            print("Error in create_bamboozle:", e)

    def create_quiz(self, vocab_words, email, user_id):
        """Generate and email an ESL quiz doc."""
        try:
            quiz_variable = 'Review Quiz'
            prompt = create_prompt(vocab_words)
            response = generate_esl_quiz(prompt, max_tokens=550)
            word_s = create_a_word_document(response)
            send_email_with_attachment(email, word_s, quiz_variable, user_id)
        except (WebDriverException, Exception) as e:
            print("Error in create_quiz:", e)

    def create_word_search(self, vocabs, email, user_id):
        """Generate and email a word search PDF."""
        try:
            wordsearch_variable = 'Wordsearch'
            wordsearch_path = make_word_search(vocabs)
            send_email_with_attachment(email, wordsearch_path, wordsearch_variable, user_id)
        except (WebDriverException, Exception) as e:
            print("Error in create_word_search:", e)

    def close(self):
        """Always close the driver gracefully."""
        try:
            self.driver.quit()
        except Exception as e:
            print("Exception on driver.quit():", e)


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

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
from flask_login import login_required, current_user

@app.route('/keep_alive', methods=['GET', 'POST'])
def keep_alive():
    conn = postgres_db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT title from kindergarten')
    ans = cursor.fetchall()
    try:
        if ans:
            print(ans)
            return 'Kept Alive'
        else:
            return 'PING NOT WORKING'
    except DatabaseError as e:
            print(f"Database error: {e}")
            return render_template('error.html', error_message="Database error occurred.")








@app.route('/', methods=['GET', 'POST'])
@login_required
def book_unit():
    total_start = time.time()
    print("book_unit: start")

    email = current_user.personal_email
    bamboozle_email = current_user.bamboozle_email
    bamboozle_password = current_user.bamboozle_password

    selected_book, selected_unit, combined_vocab = setup_bookunit()
    print(f"setup_bookunit took: {time.time() - total_start:.3f} seconds")

    try:
        book_to_units, books, kg_vocab = postgres_db.setup_function_combined()
    except DatabaseError as e:
        print(f"Database error: {e}")
        return render_template('error.html', error_message="Database error occurred.")

    if request.method == 'POST':
        print('1111111111111111111111111111111')
        print(f"FORM KEYS: {request.form.to_dict()}")

        # Safely get 'action' to avoid KeyError
        clicked = request.form.get('clickedButton', '')
        # action = request.form.get('action', '')
        print(f'{clicked} ssssssssssssssss')
        user_id = current_user.get_id()
        sid = user_sid_map.get(str(user_id))

        if not clicked:
            # If we have no action at all (maybe user pressed Enter?), just re-render
            return render_template(
                'book_unit.html',
                vocab=combined_vocab,
                books=books,
                book_to_units=book_to_units,
                kg_vocab=kg_vocab,
                selected_book=selected_book,
                selected_unit=selected_unit
            )

        if clicked == 'bamboozle':
            vocab_words = request.form.get('vocab', '')
            bamboozle_title = request.form.get('bamboozleTitle', '')

            # Emit "started"
            if sid:
                socketio.emit('bamboozle_started', {'message': 'Creating Bamboozle...'}, room=sid)

            # Kick off background
            handle_bamboozle(vocab_words, bamboozle_title, books, book_to_units,
                             kg_vocab, selected_book, selected_unit,
                             bamboozle_email, bamboozle_password)

            return jsonify({"status": "bamboozle started"})

        elif clicked == 'reviewQuiz':
            vocabs = request.form.get('vocab', '')
            if sid:
                socketio.emit('review_quiz_started', {'message': 'Creating Review Quiz...'}, room=sid)

            handle_review_quiz(vocabs, books, kg_vocab, book_to_units,
                               selected_book, selected_unit, email)
            return jsonify({"status": "review quiz started"})

        elif clicked == 'ShowVocab':
            print('**************8')
            book = request.form.get('bookName', 'None')
            unit = request.form.get('unitNumber', 'None')
            kg_category = request.form.get('kgTitle', 'KG')
            existing_vocab = request.form.get('vocab', '')



            new_combined_vocab = []

            if book != 'None':
                new_vocab = postgres_db.get_vocab(book, unit)
                new_combined_vocab.extend(new_vocab)

            if kg_category != 'NONE':
                print('1')
                print(kg_category)
                kg_vocab_list = kg_vocab.get(kg_category, [])
                print('2')
                print(kg_vocab_list)
                new_combined_vocab.extend(kg_vocab_list)
                print('3')

            if existing_vocab:
                combined_vocab = ', '.join(filter(None, [existing_vocab, ', '.join(new_combined_vocab)]))
            else:
                combined_vocab = ', '.join(str(item) for item in new_combined_vocab)

            # Re-render the template so the new vocab is visible
            return render_template(
                'book_unit.html',
                vocab=combined_vocab,
                books=books,
                book_to_units=book_to_units,
                kg_vocab=kg_vocab,
                selected_book=selected_book,
                selected_unit=selected_unit
            )

        elif clicked == 'wordSearch':
            vocabs = request.form.get('vocab', '')
            compress_vocab = vocabs.replace(' ', '')

            if sid:
                socketio.emit('wordsearch_started', {'message': 'Creating Wordsearch...'}, room=sid)

            handle_wordsearch(vocabs=compress_vocab,
                              normal_vocabs=vocabs,
                              books=books,
                              book_to_units=book_to_units,
                              kg_vocab=kg_vocab,
                              selected_book=selected_book,
                              selected_unit=selected_unit,
                              email=email)

            return jsonify({"status": "wordsearch started"})

    # GET => show page
    return render_template(
        'book_unit.html',
        vocab=combined_vocab,
        books=books,
        book_to_units=book_to_units,
        kg_vocab=kg_vocab,
        selected_book=selected_book,
        selected_unit=selected_unit
    )




def setup_bookunit():
    if 'selected_book' not in session or request.method == 'GET':
        session['selected_book'] = 'None'
    if 'selected_unit' not in session or request.method == 'GET':
        session['selected_unit'] = 'None'
    selected_book = session.get('selected_book', 'None')
    selected_unit = session.get('selected_unit', 'None')
    combined_vocab = ''
    return selected_book, selected_unit, combined_vocab


def handle_bamboozle(vocab_words, bamboozle_title, books, book_to_units, kg_vocab,
                     selected_book, selected_unit, bamboozle_email, bamboozle_password):
    if not vocab_words:
        # If missing vocab, just return None or some minimal error
        return None

    vocabs = vocab_words.split(', ')

    def run_bamboozle(driver, url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs, user_id):
        try:
            if bamboozle_email and bamboozle_password:
                driver.create_bamboozle(url, bamboozle_email, bamboozle_password, bamboozle_title, vocabs)

                # When it's done, let the user know
                sid = user_sid_map.get(str(user_id))
                if sid:
                    socketio.emit('bamboozle_done',
                                  {'message': 'Bamboozle created successfully!'},
                                  room=sid)
                else:
                    print(f'No sid found for user {user_id}')
            else:
                print('Baamboozle credentials are missing. Please update your profile.')
        except Exception as e:
            print("run_bamboozle top-level exception:", e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error', {
                    'message': f'Failed to create Bamboozle. Error: {str(e)}'
                }, room=sid)
        finally:
            driver.close()

    if vocabs:
        driver = Driver()
        user_id = current_user.get_id()
        game_create_url = 'https://www.baamboozle.com/games/create'
        socketio.start_background_task(
            run_bamboozle,
            driver,
            game_create_url,
            bamboozle_email,
            bamboozle_password,
            bamboozle_title,
            vocabs,
            user_id
        )

    # Return nothing or a small confirmation
    return True



def handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit, email):
    if not vocabs:
        return None

    def create_review_quiz(driver, vocabs, email, user_id):
        try:
            driver.create_quiz(vocabs, email, user_id)

            # When done, let user know
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('review_quiz_done',
                              {'message': f'Review Quiz sent successfully to {email}'},
                              room=sid)
            else:
                print(f'No sid found for user {user_id}')
        except Exception as e:
            print("create_review_quiz top-level exception:", e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error',
                              {'message': f'Failed to send Review Quiz. Error: {str(e)}'},
                              room=sid)
        finally:
            driver.close()

    driver = Driver()
    user_id = current_user.get_id()
    socketio.start_background_task(create_review_quiz, driver, vocabs, email, user_id)

    return True


def handle_wordsearch(vocabs, normal_vocabs, books, kg_vocab, book_to_units,
                      selected_book, selected_unit, email):
    if not vocabs:
        return None

    def run_word_search(driver, vocabs, email, user_id):
        try:
            driver.create_word_search(vocabs, email, user_id)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('wordsearch_done',
                              {'message': f'Wordsearch sent successfully to {email}'},
                              room=sid)
            else:
                print(f'No sid found for user {user_id}')
        except Exception as e:
            print("run_word_search top-level exception:", e)
            sid = user_sid_map.get(str(user_id))
            if sid:
                socketio.emit('email_error',
                              {'message': f'Failed to send wordsearch. Error: {str(e)}'},
                              room=sid)
        finally:
            driver.close()

    driver = Driver()
    user_id = current_user.get_id()
    socketio.start_background_task(run_word_search, driver, vocabs, email, user_id)

    return True



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
        openai.api_key = os.getenv("API_KEY")
        response = openai.ChatCompletion.create(
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
    puzzle = WordSearch(vocab)
    puzzle.show()
    filename = 'word_search.pdf'
    puzzle.save(filename)
    wordsearch_path = os.path.abspath(filename)
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
    user_id = None
    for uid, user_sid in list(user_sid_map.items()):
        if user_sid == sid:
            user_id = uid
            break
    if user_id:
        user_sid_map.pop(user_id, None)
        print(f'User {user_id} disconnected')


@socketio.on('connect')
def handle_connection():
    print('Client connected')


def send_email_with_attachment(to_email, path, content, user_id, file_path=None):
    from_email = os.getenv('E_NAME')
    password = os.getenv('E_PASS')

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = f"Here is your {content} :)"

    body_content = f"Please find the attached {content}."
    msg.attach(MIMEText(body_content, 'plain'))

    file_path = path if path else file_path

    if file_path:
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'

            with open(file_path, "rb") as attachment:
                part = MIMEBase(*mime_type.split("/"))
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(file_path)}"'
            )
            msg.attach(part)

        except Exception as e:
            print(f'Failed to attach file: {e}')
            socketio.emit('email_error', {'message': f'Failed to attach file: {str(e)}'})

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())

        sid = user_sid_map.get(str(user_id))
        if sid:
            socketio.emit('email_sent', {'message': f'{content} sent successfully to {to_email}'}, room=sid)
        else:
            print(f'No sid found for user {user_id}')
        print(f'Email sent successfully to {to_email}')

    except Exception as e:
        sid = user_sid_map.get(str(user_id))
        if sid:
            socketio.emit('email_error', {
                'message': f'Failed to send {content} to {to_email}. Error: {str(e)}'
            }, room=sid)
        else:
            print(f'No sid found for user {user_id}')
        print(f'Failed to send email: {e}')

    finally:
        server.quit()
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f'{file_path} deleted successfully.')
            except Exception as e:
                print(f'Error deleting file: {e}')


if __name__ == '__main__':
    socketio.run(app, debug=debug)
