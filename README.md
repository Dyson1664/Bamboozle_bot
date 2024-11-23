# ESL Game Creation App

A Flask-based web application that automates the creation of interactive ESL games and educational content, enhancing language learning experiences for educators and students.

## Features

* **Vocabulary Management**: Store and retrieve vocabulary organized by books, units, and kindergarten topics from a PostgreSQL database.
* **Interactive Game Creation**: Automate the creation of Baamboozle games using Selenium, pairing vocabulary words with images.
* **Content Generation with GPT**: Generate ESL quizzes and comprehension questions using OpenAI's GPT models.
* **Word Search Creation**: Create word searches from selected vocabulary.
* **User Authentication**: Secure registration and login for users.
* **Real-Time Notifications**: Receive instant updates on game creation and content generation via Socket.IO.

## Prerequisites

* **Python**: 3.6 or higher
* **Google Chrome**: For Selenium automation
* **Chromedriver**: Compatible with your Chrome version
* **PostgreSQL**: For database management
* **OpenAI API Key**: For GPT-powered content generation
* **SMTP Server Access**: For email functionalities
* **Environment Variables**: For configuration details

## Installation

### 1. Clone the Repository:

git clone https://github.com/dyson1664/Bamboozle_bot.git
cd Bamboozle_bot

### 2. Install Dependencies:

pip install -r requirements.txt

### 3. Set Up Database:

Create a PostgreSQL database.
Update the DATABASE_URL in your environment variables.

## Configuration
Create a .env file with the following variables:

```ini
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
EMAIL=your-email@example.com
PASSWORD=your-email-password
API_KEY=your-openai-api-key
E_NAME=your-email@example.com
E_PASS=your-email-password
FERNET_KEY=your-fernet-key
CHROMEDRIVER_PATH=/path/to/chromedriver
GOOGLE_CHROME_BIN=/path/to/google-chrome
```


## Environment Variables:

* **SECRET_KEY:** A secret key for Flask session management
* **DATABASE_URL:** Connection string for your PostgreSQL database
* **EMAIL and PASSWORD:** Credentials for the email account used to send emails from the app
* **API_KEY:** Your OpenAI API key for accessing GPT models
* **FERNET_KEY:** A key used by the cryptography library to encrypt sensitive data

## Running the Application
* **Start the Flask application:**
```python main.py```
Access the app at http://localhost:5000
Usage

* **Register:** Sign up with a username, password, and email
* **Login:** Access your account
* **Select Vocabulary:** Choose books, units, and topics
* **Create Games:** Generate Baamboozle games, quizzes, and word searches
* **Receive Content:** Quizzes and word searches are emailed to you

