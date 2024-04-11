import re
import time
import logging
import psycopg2
from config import *
from bs4 import BeautifulSoup as soup
# Libraries below are for webscraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException, ElementClickInterceptedException

# Setting basic logging to the terminal
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s ')

# URL with a set filter to get job offers from
FILTER_URL = 'https://simplify.jobs/jobs?experience=Internship'


def setup_driver():
    """
    Setting up the driver and creating Options for future updates

    :return driver: (selenium.webdriver) Mounted Firefox driver
    """
    # Geckodriver in the path is expected
    options = Options()
    driver = webdriver.Firefox(options=options)
    return driver


def login(driver):
    """
    Login to Simplify website with the driver.
    Avoid recaptcha manually if needed, and press enter key to continue.

    :param driver: (selenium.webdriver)
    :return: Logged in driver of the Firefox application
    """
    logging.info('Driver setup complete, logging to the website...')
    # Getting a login page and waiting till it's loaded
    driver.get("https://simplify.jobs/auth/login")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.flex")))

    # Inputting Username and password and clicking the login button
    inputs = driver.find_elements(By.CSS_SELECTOR, "input.form-input")
    inputs[0].send_keys(USERNAME)
    inputs[1].send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button.flex").click()

    # Wait for the successful login. If not successful (recaptcha, etc.) wait for the manual resolvent and continue
    while True:
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, "a.rounded-full.bg-primary-light")))
            logging.info("Login successful, processing to jobs...")
            break  # Exit loop if login is successful
        except TimeoutException:
            logging.info((
                "Login unsuccessful or CAPTCHA encountered. Please solve "
                "if CAPTCHA is present and press enter to continue"))
            input("Press Enter after resolving issues to retry... ")


def scroll_and_load_jobs(driver, conn, cur):
    """
    Scrolls through the job listings page, loads more job listings, and scrapes the data.
    The scraped data is extracted from each job listing, and the data is then stored into the database.
    This function scrolls until no more job listings are left on the website.

    :param driver : selenium.webdriver) Browser driver to interact with the webpage.
    :param conn: (psycopg2.extensions.connection) Connection to the PostgreSQL database.
    :param cur: (psycopg2.extensions.cursor) Cursor associated with the database connection.
    :return: None
    """
    # Go to the main Job page
    driver.get(FILTER_URL)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR, 'div.bg-white.rounded-md')))

    start_block_n = 0
    while True:
        all_job_blocks = driver.find_elements(
                By.CSS_SELECTOR, "div.bg-white.rounded-md")
        section_job_blocks = all_job_blocks[start_block_n: start_block_n + 21]
        if len(section_job_blocks) == 0:
            break

        for offer in section_job_blocks:
            # Iterate through all job offers in a section and click on "Detail"
            offer.find_element(By.CSS_SELECTOR, 'span.ml-2').click()

            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 'button.text-lg')))

            # Write information about one job offer to the variable
            inline_offer_block = soup(driver.find_element(
                By.CSS_SELECTOR, 'div.relative.h-screen'
            ).get_attribute('outerHTML'), 'lxml')

            conn, cur = grab_offer_info(
                offer, inline_offer_block, driver.current_url, conn, cur)

            # Close job offer info
            start_block_n += 1
            driver.find_element(By.CSS_SELECTOR, 'button.float-right').click()
            WebDriverWait(driver, 30).until(
                EC.invisibility_of_element((
                    By.CSS_SELECTOR, 'div.fixed')))

        try:
            section_job_blocks[-1].send_keys(Keys.PAGE_DOWN)
        except ElementNotInteractableException:
            time.sleep(0.5)


def grab_offer_info(offer, inline_offer_block, url, conn, cur):
    """
    This function grabs the information about the job offer from the offer, inline_offer_block, and url.
    It further proceeds to store this information into the database 'conn' with cursor 'cur'.

    :param offer: (selenium.webdriver) Information about the current job offer within the webpage
    :param inline_offer_block: (BeautifulSoup object) HTML object containing job offer information
    :param url: (str) URL of the job offer
    :param conn: (psycopg2.extensions.connection) Connection to the PostgreSQL database
    :param cur: (psycopg2.extensions.cursor) Cursor associated with the database connection
    :return: conn, cur: Connection and cursor related to the database after execution
    """
    ...
    offer_id = re.search(r'/([0-9a-fA-F-]{36})/', url).group(1).strip('/')
    job_data = {
        'id': offer_id,
        'position_name': offer.find_element(By.CSS_SELECTOR, 'h3').text,
        'company_name': offer.find_element(By.CSS_SELECTOR, 'h4').text,
        'locations': offer.find_element(By.CSS_SELECTOR, 'p').text,
        'experience_level': [
            i.text for i in inline_offer_block.select('div.bg-primary-light')
        ] if inline_offer_block.select('div.bg-primary-light') else 'Intern',
        'desired_skills': [sk.text for sk in inline_offer_block.select_one(
            'div.mb-3').select('div.mt-3')],
        'categories': [cat.text for cat in inline_offer_block.find(
            'div', attrs={'data-state': 'closed'}).select('div.mt-3')],
        'employee_count': inline_offer_block.select_one(
            'p.mt-1').text.replace('employees', '').strip(),
        'company_website': inline_offer_block.select_one(
            'a.text-stone-600')['href'],
        'company_stage': None,
        'company_funding': extract_funding(inline_offer_block),
        'foundation_year': None,
        'company_industries': [ind.text for ind in inline_offer_block.select(
            'div.mb-1 div.mt-3')]
    }
    if inline_offer_block.select('div.py-5 h1'):
        job_data['company_stage'] = inline_offer_block.select(
            'div.py-5 h1')[0].text
        try:
            job_data['foundation_year'] = int(inline_offer_block.select(
                'div.py-5 h1')[2].text)
        except ValueError:
            job_data['foundation_year'] = None

            # build a query for insertion
    try:
        cur.execute(INSERT_DATA_QUERY, job_data)
        conn.commit()
        logging.info(f'{offer_id} is added to database')

    except psycopg2.errors.UniqueViolation as e:
        logging.info(f'{offer_id} is already in database')
        conn.rollback()

    return conn, cur


def extract_funding(inline_offer_block):
    """
    Extracts the funding information from the inline offer block if it is present.

    :param inline_offer_block: (BeautifulSoup object) HTML object containing job offer information.
    :return: funding (float) Amount of funding the company has raised, represented in numerical format.
    """
    funding_elements = inline_offer_block.select('div.py-5 h1')
    funding_factors = {'K': 1e3, 'M': 1e6, 'B': 1e9}
    if not funding_elements:
        return None

    funding = ''.join(e for e in funding_elements[1].text
                      if e.isalnum() or e == '.')

    for suffix, multiplier in funding_factors.items():
        if suffix in funding:
            funding = funding.replace(suffix, '')
            return int(float(funding) * multiplier)

    try:
        return int(funding)
    except (TypeError, ValueError):
        return None


def main():
    """
    After launching this script initiates connection with a PostgreSQL database,
    which is used for storage of scraped data. With the connection to the database,
    script launches Selenium driver, logins with it to Simplify.jobs, and starts to
    iterate through all available job offers on the filtered URL /jobs page. For the
    purpose of this script "?experience=Internship" filter was used. The script
    endlessly scrolls through the page until its end is reached, and opens up
    every job offer available, grabbing data from it and instantly uploading
    to the database. After all jobs are parsed, the connection to database and driver closes.
    """
    logging.info('Starting script, connecting to database')
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    try:
        driver = setup_driver()
        login(driver)
        scroll_and_load_jobs(driver, conn, cur)
        logging.info('Finished collecting jobs')
    finally:
        logging.info('Closing database connection')
        cur.close()
        conn.close()
        driver.close()


if __name__ == "__main__":
    main()
