import time
import schedule
import threading
from selenium import webdriver
from bs4 import BeautifulSoup
import csv
from flask import Flask, render_template

app = Flask(__name__)

# Define the URL
url = "https://www.bseindia.com/corporates/ann.html"

def scrape_data():
    # Set up the Selenium webdriver
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36")
    options.add_argument("headless")  # Run in headless mode
    options.add_argument("--window-size=1920,1080") 
    driver = webdriver.Chrome(options=options)

    # Navigate to the website
    driver.get(url)
    driver.implicitly_wait(10)

    # Wait for the element to be present
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//table[@ng-repeat='cann in CorpannData.Table']"))
    )

    # Get the HTML content
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Find all the table rows with the desired data
    table_rows = soup.find_all('table', {'ng-repeat': 'cann in CorpannData.Table'})

    # Create a list to store the data
    data = []

    # Iterate over the table rows and extract the data
    for row in table_rows:
        for tr in row.find_all('tr'):
            for td in tr.find_all('td', {'class': 'tdcolumngrey'}):
                span_element = td.find('span')  # Search for any span element
                if span_element:
                    text = span_element.text.strip()
                    data.append([text])

    # Filter the data that contains the word "meet"
    filtered_data = [row for row in data if "meet" in row[0].lower()]

    # Remove duplicates from the filtered data
    unique_filtered_data = [list(x) for x in set(tuple(x) for x in filtered_data)]

    # Close the browser window
    driver.quit()

    return unique_filtered_data

def fetch_data():
    unique_filtered_data = scrape_data()
    
    # Save the unique filtered data to a CSV file
    with open(r'\\172.16.1.85\Shared\Hritik\bse news\filtered_data.csv', "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(unique_filtered_data)

    return unique_filtered_data

@app.route('/')
def index():
    unique_filtered_data = fetch_data()  # Fetch data when the route is accessed
    return render_template('index.html', unique_filtered_data=unique_filtered_data)

# Schedule the data fetching
schedule.every(30).seconds.do(fetch_data)

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