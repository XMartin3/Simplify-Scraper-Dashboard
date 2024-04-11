This is a web scraping project which extracts internship job postings from the Simplify Jobs website (https://simplify.jobs/) and stores this data in a PostgreSQL database. Along with data extraction, an interactive Dash-based job dashboard is also provided for a user-friendly visualization of the scraped data.

Project consists of the following Python files:
config.py: Contains necessary configurations such as database parameters, Simplify Jobs account credentials, and the SQL query for data insertion.
parse_simplify.py: This is the main script which uses Selenium and BeautifulSoup to scrape internship job listings from the Simplify Jobs website and stores them in the database.
create_dashboard.py: This script utilizes Dash and Plotly to create an interactive dashboard that visualizes the data stored in the database.

Setup and Usage:
Clone the repository to your local machine.
Install the necessary Python packages listed in the requirements.txt file:
pip install -r requirements.txt 
Modify the config.py file as per your database setup and Simplify Jobs account credentials.
Run parse_simplify.py to scrape the internship job data:
python parse_simplify.py 
Run create_dashboard.py to start the dashboard:
python create_dashboard.py 
Requirements
This project requires Python 3.12.2 or above and the following Python libraries:
selenium
beautifulsoup4
psycopg2-binary
pandas
dash
plotly ...plus any other dependencies your application may need.
Contributing:
Contributions are welcomed. If you wish to contribute, please open an issue first to discuss your proposed changes.
License:
This project is licensed under the terms of the MIT license.
