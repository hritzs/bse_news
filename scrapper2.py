import time
import schedule
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # Import TimeoutException
from bs4 import BeautifulSoup
import csv
from flask import Flask, render_template
import datetime
import re
import requests
import logging

# Set the logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# Define the URL
url = "https://www.bseindia.com/corporates/ann.html"

# Define the scrip codes
scrip_codes = [
    '524208', '500002', '500488', '540691', '535755', '500410', '512599', '532921', '539523', '500425', 
    '508869', '500877', '500477', '500820', '532830', '500027', '540611', '524804', '532215', '532977', 
    '532978', '500034', '502355', '500038', '541153', '532134', '500043', '500049', '509480', '500493', 
    '532454', '500103', '532523', '500530', '500547', '500825', '532400', '532483', '511196', '500085', 
    '511243', '500087', '533278', '532541', '500830', '531344', '506395', '539876', '532210', '500480', 
    '500096', '542216', '506401', '532488', '540699', '532868', '500124', '505200', '500495', '500086', 
    '500469', '532155', '532296', '532754', '500670', '532424', '533150', '532482', '500300', '539336', 
    '541154', '517354', '532281', '541729', '500180', '540777', '500182', '500440', '513599', '500104', 
    '500696', '532174', '540716', '540133', '532822', '539437', '540750', '532514', '500850', '542726', 
    '539448', '532187', '534816', '500209', '530965', '524494', '542830', '500875', '532286', '532644', 
    '500228', '533155', '500247', '539524', '540222', '500253', '500510', '533519', '540005', '540115', 
    '500257', '500520', '532720', '531213', '531642', '532500', '534091', '542650', '500271', '539957', 
    '517334', '526299', '500290', '533398', '532234', '532777', '532504', '500790', '526371', '532555', 
    '533273', '532466', '500312', '532827', '500302', '533179', '532522', '532810', '500331', '523642', 
    '532461', '542652', '532898', '532689', '500260', '540065', '532955', '500325', '500113', '543066', 
    '540719', '500112', '500387', '511218', '500550', '503806', '524715', '532733', '539268', '500770', 
    '500483', '500800', '500570', '500400', '500470', '532540', '532755', '500114', '500420', '500251', 
    '532343', '532478', '532538', '532432', '512070', '500295', '500575', '507685', '532321'
]

def scrape_data():
    # Set up the Selenium webdriver
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")
    options.add_argument("headless")  # Run in headless mode
    options.add_argument("--window-size=1920,1080") 
    driver = webdriver.Chrome(options=options )

    # Navigate to the website
    driver.get(url)
    driver.implicitly_wait(10)

    # Wait for the page to finish loading
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            driver.execute_script("return document.readyState === 'complete';")
            break
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

    # Wait for the element to be present
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[@ng-repeat='cann in CorpannData.Table']"))
            )
            break
        except TimeoutException:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

    # Get the HTML content
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find all the table rows with the desired data
    table_rows = soup.find_all('table', {'ng-repeat': 'cann in CorpannData.Table'})

    # Create a list to store the data
    data = []

    # Iterate over the table rows and extract the data
    for row in table_rows:
        company_name = None
        scrip_code = None
        announcement_details = None
        pdf_link = None
        disseminated_time = None

        for tr in row.find_all('tr'):
            # Extract the main data
            for td in tr.find_all('td', {'class': 'tdcolumngrey'}):
                span_element = td.find('span')  # Search for any span element
                if span_element:
                    text = span_element.text.strip()
                    # Extract company name, scrip code, and announcement details
                    match = re.match(r'(.*) - (\d+) - (.*)', text)
                    if match:
                        company_name = match.group(1)
                        scrip_code = match.group(2)
                        announcement_details = match.group(3)

            # Extract the PDF link
            pdf_link_element = tr.find('td', {'class': 'tdcolumngrey', 'ng-if': 'cann.PDFFLAG==0 && cann.ATTACHMENTNAME'})
            # print(pdf_link)
            if pdf_link_element and pdf_link_element.find('a'):
                pdf_link = "https://www.bseindia.com/" + pdf_link_element.find('a')['href']

            # Extract the Exchange Disseminated Time
            if tr.has_attr('ng-if') and tr['ng-if'] == 'cann.TimeDiff':
                disseminated_time_element = tr.find('b', {'class': 'ng-binding'})
                if disseminated_time_element:
                    disseminated_time = disseminated_time_element.text.strip()


        if company_name and scrip_code and announcement_details:
            data_row = [company_name, scrip_code, announcement_details, disseminated_time, pdf_link]
            data.append(data_row)

    # Close the browser window
    driver.quit()

    return data

def update_data():
    data = scrape_data()
    with open('data.csv', "a", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)

def fetch_data():
    with open('data.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [row for row in reader]

    # Filter the data that contains the word "board meeting" and the scrip code
    filtered_data = []
    for row in data:
        if len(row) > 2 and "board meeting" in row[2].lower() and row[1] in scrip_codes:
            filtered_data.append(row)

    # Remove duplicates from the filtered data, considering the PDF link
    unique_filtered_data = []
    news_content_set = set()
    for row in filtered_data:
        news_content = row[2].lower()  # Use the news content as the key
        if news_content not in news_content_set:
            # Find the row with a PDF link
            pdf_row = next((r for r in filtered_data if r[2].lower() == news_content and r[4]), None)
            if pdf_row:
                unique_filtered_data.append(pdf_row)
            else:
                unique_filtered_data.append(row)  # Append the first occurrence if no PDF link is found
            news_content_set.add(news_content)

    # Sort the data by timestamp
    unique_filtered_data.sort(key=lambda x: x[3] if len(x) > 3 else datetime.datetime.min, reverse=True)  # Sort by disseminated time

    # Download the PDF file and check for the word "result"
    for row in unique_filtered_data:
        if len(row) > 4 and row[4]:
            # pdf_url = row[4]
            pdf_url = row[4].replace('//', '/') 
            try:
                # Download the PDF file
                headers = {'User -Agent': 'Mozilla/5.0'}
                response = requests.get(pdf_url, stream=True, headers=headers)
                response.raise_for_status()  # Raise an error for bad responses

                # Save the PDF to a temporary file
                temp_pdf_path = 'temp.pdf'
                with open(temp_pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                # Read the PDF file
                pdf_file = PyPDF2.PdfReader(temp_pdf_path)
                text = ''
                for page in range(len(pdf_file.pages)):
                    text += pdf_file.pages[page].extract_text()

                # Check for the word "result"
                if 'result' in text.lower():
                    row.append('Yes')
                else:
                    row.append('No')

                # Clean up the temporary file
                os.remove(temp_pdf_path)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"404 Error: PDF not found at {pdf_url}")
                    row.append('Error: PDF not found')
                else:
                    print(f"Error extracting word 'result' from PDF: {e}")
                    row.append('Error')
            except Exception as e:
                print(f"Unexpected error: {e}")
                row.append('Error')

    with open('filtered_data.csv', "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(unique_filtered_data)
    return unique_filtered_data

@app.route('/')
def index ():
    unique_filtered_data = fetch_data()  # Fetch data when the route is accessed
    return render_template('index.html', unique_filtered_data=unique_filtered_data)

# Schedule the data fetching
schedule.every(60).seconds.do(update_data)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

thread = threading.Thread(target=run_schedule)
thread.daemon = True
thread.start()

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        thread.join()  # Wait for the scheduler thread to exit
        print("Scheduler stopped.")