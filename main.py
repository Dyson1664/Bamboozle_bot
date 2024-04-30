from flask import Flask, render_template, request, session
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

from openai import OpenAI
from docx import Document
from word_search_generator import WordSearch
import threading

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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
client = OpenAI(api_key=os.environ['API_KEY'])

# os.environ["GOOGLE_CHROME_BIN"] = r"C:\Users\PC\Downloads\chrome-win64 (3)\chrome-win64\chrome.exe"

# os.environ["CHROMEDRIVER_PATH"] = r"C:\Users\PC\Downloads\chromedriver-win64 (3)\chromedriver-win64\chromedriver.exe"
class Driver:
    def __init__(self):
        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument('--start-maximized')
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--no-sandbox")
        # self. driver = webdriver.Chrome(options=chrome_options)

        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)



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

        except WebDriverException as e:
            print("Exception occurred while interacting with the element: ", e)

    #loop though adding vocab and clicking pictures
    def create_game_part_two(self, vocabs):
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

            close_gpt = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//*[@id=\"beamerAnnouncementBar\"]/div[2]/div[2]")
                )
            )
            close_gpt.click()

        except Exception as e:
            print('Could not click the cookie button', e)

    def create_bamboozle(self, url, EMAIL, PASSWORD, title, vocabs):
        self.sign_in(url, EMAIL, PASSWORD)
        self.create_game(title)
        self.create_game_part_two(vocabs)

    def create_quiz(self, vocab_words, API_KEY):
        prompt = create_prompt(vocab_words)
        response = generate_esl_quiz(API_KEY, prompt, max_tokens=550)
        path = create_a_word_document(response)
        send_email_with_attachment(path)


    def create_word_search2(self, vocab):
        puzzle = create_word_search(vocab)
        send_email_with_attachment(puzzle)

    def close(self):
        self.driver.quit()

# main webpage
@app.route('/', methods=['GET', 'POST'])
def book_unit():
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
            vocab_words = request.form.get('vocab', '')
            # vocabs = vocab_words.split(', ') if vocab_words else []

            title = request.form.get('bamboozleTitle', '')
            return handle_bamboozle(vocab_words, title, books, book_to_units, kg_vocab, selected_book, selected_unit)

        elif request.form['action'] == 'reviewQuiz':
            vocabs = request.form.get('vocab', '')
            return handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit)

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
            vocabs = request.form.get('vocab')

            local_driver = Driver()
            word_search_thread = threading.Thread(target=local_driver.create_word_search2, args=(vocabs,))
            word_search_thread.start()

            return render_template('book_unit.html', vocab=vocabs, books=books, kg_vocab=kg_vocab, book_to_units=book_to_units,
                                   selected_book=selected_book, selected_unit=selected_unit)

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



def handle_bamboozle(vocab_words, bamboozle_title, books, book_to_units, kg_vocab, selected_book, selected_unit):
    if not vocab_words:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)
    # Split vocab words into a list
    vocabs = vocab_words.split(', ')
    # Initialize Driver and start bamboozle thread
    local_driver = Driver()
    thread = threading.Thread(target=local_driver.create_bamboozle,
                              args=(url, EMAIL, PASSWORD, bamboozle_title, vocabs))
    thread.start()
    # Return the template with the updated vocabulary
    return render_template('book_unit.html',  vocab=vocab_words, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab, selected_book=selected_book, selected_unit=selected_unit)

def handle_review_quiz(vocabs, books, kg_vocab, book_to_units, selected_book, selected_unit):
    if not vocabs:
        return render_template('book_unit.html', error="Vocabulary is required.", books=books, kg_vocab=kg_vocab,
                               book_to_units=book_to_units, selected_book=selected_book, selected_unit=selected_unit)

    local_driver = Driver()
    quiz_thread = threading.Thread(target=local_driver.create_quiz, args=(vocabs, API_KEY))
    quiz_thread.start()

    return render_template('book_unit.html', vocab=vocabs, books=books, book_to_units=book_to_units, kg_vocab=kg_vocab,
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

def generate_esl_quiz(API_KEY, prompt, max_tokens=550):
    prompt = prompt

    client = OpenAI(api_key=API_KEY)

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Specify the GPT-4 model
            messages=[
                {"role": "system", "content": "You are a skilled ESL teacher."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred: {e}"

def create_word_search(vocab):
    puzzle = WordSearch(vocab)
    filename = 'word_search.pdf'
    puzzle.save(filename)

    # location = puzzle.save(path=r"C:\Users\PC\Desktop\work_webpage\Bamboozle_ESL-game\word_search.pdf")
    return os.path.abspath(filename)


def create_a_word_document(text):
    doc = Document()
    doc.add_paragraph(text)
    filename = 'word_doc.docx'
    doc.save(filename)
    path = os.path.abspath(filename)
    return path

def send_email_with_attachment(file_path):
    send_from = E_NAME
    password = E_PASS
    send_to = E_NAME
    subject = f'Quiz'
    body = ':)'
    file_path = file_path
    server = None
    try:
        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(send_from, password)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = send_to
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        # Open the file to be sent
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(file_path))
            msg.attach(part)

        # Send the email
        server.send_message(msg)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if server:
            server.quit()

        # Attempt to delete the file
        try:
            print("Deleting the document...")
            os.remove(file_path)
            print(f"Document {file_path} deleted successfully.")
        except Exception as e:
            print(f"Error deleting file: {e}")



if __name__ == '__main__':
    app.run(debug=True, port=5001, use_reloader=False)

#finished :)



