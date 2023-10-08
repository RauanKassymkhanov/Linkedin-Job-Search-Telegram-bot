from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from urllib.parse import quote
from selenium.webdriver.chrome.service import Service
import random
import logging
import pyshorteners
from selenium.webdriver.chrome.options import Options

s = pyshorteners.Shortener()

TOKEN: Final = '6666623950:AAEWzFoPkVdd-zwFwT7Bbb8Jfo7NLkD8Zko'
BOT_USERNAME: Final = '@LinkedinJobScraper_bot'

# LinkedIn job search URL
LINKEDIN_JOB_SEARCH_URL = 'https://www.linkedin.com/jobs/search/'

# Specify the path to your WebDriver executable (e.g., Chrome WebDriver)
WEBDRIVER_PATH = 'C:/Users/user/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe'


chrome_options = Options()
chrome_options.add_argument("--lang=en-US")  # Set the language to English
chrome_options.add_argument("--start-maximized")  # Maximize the browser window (optional)


service = Service(executable_path=WEBDRIVER_PATH)
# Initialize the WebDriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Set implicit wait to handle dynamic page elements
driver.implicitly_wait(10)

def format_job_list(job_list):
    result = ""
    for job in job_list:
        for key, value in job.items():
            result += f"{key}: {value}\n"
        result += "\n"  
    return result

# Telegram Bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Welcome to LinkedIn Job Search bot!')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('To search for jobs, use the /search command like this: /search python developer in Hungary')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = context.args
    if len(user_input) < 1:
        await update.message.reply_text('Please provide a query, e.g., /search python developer in Hungary')
    else:
        user_input = " ".join(user_input)
        parts = user_input.split(" in ")
        if len(parts) == 2:
            job = quote(parts[0])
            location = quote(" in ".join(parts[1:]))
            job_results = scrape_linkedin_jobs(job, location)

            if job_results:
                response = "".join(job_results)  # Join the links with newlines
            else:
                response = "No job listings found."

            await update.message.reply_text(response)
        else:
            await update.message.reply_text('Please provide both query and location, e.g., /search python developer in Hungary')

# Scrape job listings from LinkedIn using Selenium
def scrape_linkedin_jobs(job, location):
    search_url = f"{LINKEDIN_JOB_SEARCH_URL}?keywords={job}&location={location}"
    driver.get(search_url)

    # Wait for the page to load
    time.sleep(5)  # Adjust the sleep time as needed

    # Extract job listings
    job_results = extract_job_listings()

    return job_results  # Limit to the first 5 job listings

# Extract job listings using Selenium and BeautifulSoup
def extract_job_listings():
    jobs = []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_listings = soup.find_all(
        "div",
        class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
    )

    try:
        job_count = 0  # Initialize a counter for extracted jobs
        for job in job_listings:
            # Extract job details
            job_title = job.find("h3", class_="base-search-card__title").text.strip()
            job_company = job.find("h4", class_="base-search-card__subtitle").text.strip()
            job_location = job.find("span", class_="job-search-card__location").text.strip()
            apply_link = job.find("a", class_="base-card__full-link")["href"]

            shortened_link = s.tinyurl.short(apply_link)

            # Navigate to the job posting page and scrape the description
            driver.get(apply_link)

            # Sleep for a random duration between 5 and 10 seconds
            time.sleep(random.choice(list(range(5, 11))))

            # Use try-except block to handle exceptions when retrieving job description
            
            # Add job details to the jobs list
            jobs.append(
                {
                    "Job title": job_title,
                    "Company name": job_company,
                    "Location": job_location,
                    "Link": shortened_link,   
                }
            )
            
            
            # Increment the job counter
            job_count += 1

            # Log the scraped job with company and location information
            logging.info(f'Scraped "{job_title}" at {job_company} in {job_location}...')

            if job_count == 5:
                # If 5 jobs have been extracted, stop and return the jobs list
                break

    # Catching any exception that occurs in the scraping process
    except Exception as e:
        # Log an error message with the exception details
        logging.error(f"An error occurred while scraping jobs: {str(e)}")

    formatted_text = format_job_list(jobs)

    return formatted_text



# Other response handling functions
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, '').strip()
            response = handle_response(new_text)
        else:
            return
    else:
        response = handle_response(text)

    await update.message.reply_text(response)

def handle_response(text: str) -> str:
    processed = text.lower()

    if 'hello' in processed:
        return 'Hey'
    if 'how are you?' in processed:
        return 'I am doing good, thanks!'

    return 'I do not understand what you wrote...'

# Errors
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('search', search_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Poll the bot
    print('Polling...')
    app.run_polling(poll_interval=3)
