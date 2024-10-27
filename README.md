# Educational Vocabulary App Bot

## Overview
This Flask-based web application enhances educational processes by automating the creation of interactive vocabulary games and content. Leveraging advanced automation technologies such as Selenium and integrating OpenAI's GPT models, this app serves as a dynamic tool for educators.

## Features

- **Vocabulary Management**: Manages vocabulary storage and retrieval from a PostgreSQL database, organized by book titles and unit numbers.
- **Interactive Game Creation**: Uses a Selenium-based bot to automate the creation of Bamboozle games, pairing vocabulary words with images to enhance learning engagement.
- **Content Generation with GPT**: Employs OpenAI's GPT to generate stories and comprehension questions which are then emailed directly to educators.
- **Word Search Creation**: Automatically generates word searches from selected vocabulary, enhancing classroom learning experiences.
- **User Authentication**: Includes a login feature for user authentication, ensuring that only registered users can access certain functionalities.

## Prerequisites

- Python 3.6 or higher
- Flask
- Selenium with ChromeDriver for web automation
- SMTP server access for email functionalities
- OpenAI API key

## Installation

1. **Clone the repository**:
   ```sh
   git clone https://github.com/Dyson1664/Bamboozle_ESL-game.git
2. pip install -r requirements.txt
3. Set up a PostgreSQL database and update the database credentials in the `config.py` file.
## Configuration

### Configure Environment
Configure the necessary environment variables in a .env file or directly in your system's environment:
```plaintext
EMAIL=your-email@example.com
PASSWORD=your-email-password
API_KEY=your-openai-api-key
E_PASS=email-password
E_NAME=email-username
DATABASE_URL=your-database-url
```

Replace each placeholder with your actual data.

### Update ChromeDriver Path
Update the path to `chromedriver.exe` in the `Driver` class to match your system's ChromeDriver location.

## Running the Application
After completing the installation and configuration, start the server by running:

```
python app.py
```
## User Authentication
### Register
Navigate to http://localhost:5000/register and enter a username, password, and email to create a new account.

### Login
Navigate to http://localhost:5000/login and enter your username and password to log in.

Navigate to http://localhost:5000/ to access the application.
