
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import requests
import re

# constants:
url = "https://appbrewery.github.io/Zillow-Clone/"

# send request to the website:
response = requests.get(url)
html_doc = response.text

# parse the html:
soup = BeautifulSoup(html_doc, 'html.parser')

# regex patterns for cleaning price strings:
cleanup_pattern = re.compile(r'\+|/mo')
price_only_pattern = re.compile(r'\$\d+[\d,]*')

# find all property listings and iterate through each one:
property_listings = []
for article in soup.find_all('article', class_='StyledPropertyCard-c11n-8-84'):
    # extract url:
    link_element = article.find('a', class_='StyledPropertyCardDataArea-anchor', href=True)
    url_link = link_element['href'] if link_element else 'No URL Found'

    # extract price:
    price_element = article.find('span', class_='PropertyCardWrapper__StyledPriceLine')
    price_text = price_element.text if price_element else 'No Price Found'
    cleaned_price = cleanup_pattern.sub('', price_text)
    # Extract only the price part, ignoring any extra text like '1bd':
    price_only_match = price_only_pattern.search(cleaned_price)
    cleaned_price = price_only_match.group() if price_only_match else cleaned_price

    # extract address:
    address_element = article.find('address', {'data-test': 'property-card-addr'})
    address = address_element.text.strip() if address_element else 'No Address Found'

    # append a dictionary for each listing to the property_listings list:
    property_listings.append({
        'url': url_link,
        'price': cleaned_price,
        'address': address
    })

# initialize selenium webdriver:
chrome_options = Options()
# chrome_options.add_argument("--headless")  # uncomment this line to run in headless mode
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

form_url = "https://forms.gle/72vXFXP9gjXq3Qio8"
driver.get(form_url)


# function to attempt finding an element using different methods:
def find_element(driver, methods):
    for method, selector in methods:
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((method, selector)))
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((method, selector)))
            return element
        except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
            continue
    raise Exception("Element not found using provided methods.")


print(f"Processing {len(property_listings)} listings...")

# iterate over all property listings and fill out the google form:
for index, property in enumerate(property_listings, 1):
    address_field = find_element(driver, [
        (By.CSS_SELECTOR, "input[aria-labelledby='i1']"),
        (By.XPATH, "//*[@id='mG61Hd']/div[2]/div/div[2]/div[1]/div/div/div[2]/div/div[1]/div/div[1]/input")
    ])
    address_field.clear()
    address_field.send_keys(property['address'])

    price_field = find_element(driver, [
        (By.CSS_SELECTOR, "input[aria-labelledby='i5']"),
        (By.XPATH, "//*[@id='mG61Hd']/div[2]/div/div[2]/div[2]/div/div/div[2]/div/div[1]/div/div[1]/input")
    ])
    price_field.clear()
    price_field.send_keys(property['price'])

    url_field = find_element(driver, [
        (By.CSS_SELECTOR, "input[aria-labelledby='i9']"),
        (By.XPATH, "//*[@id='mG61Hd']/div[2]/div/div[2]/div[3]/div/div/div[2]/div/div[1]/div/div[1]/input")
    ])
    url_field.clear()
    url_field.send_keys(property['url'])

    submit_button = find_element(driver, [
        (By.CSS_SELECTOR, ".NPEfkd.RveJvd.snByac"),
        (By.XPATH, "//*[@id='mG61Hd']/div[2]/div/div[3]/div[1]/div[1]/div/span/span")
    ])
    submit_button.click()
    time.sleep(0.4)  # wait after submission

    # click on "Submit another response" link, if available
    try:
        submit_another = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Submit another response')]")))
        submit_another.click()
    except TimeoutException:
        print("No more 'Submit another response' link found.")
        break  # exit the loop if there's no link to submit another response

    print(f"Processed Listing #{index}: URL: {property['url']}, Price: {property['price']}, Address: {property['address']}")

    time.sleep(0.4)  # wait before filling out the next form

# print completion message
print(f"Completed processing all {len(property_listings)} listings.")

input("Press Enter to close the browser...")
driver.quit()


