import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Path to your chromedriver executable
CHROMEDRIVER_PATH = '/Users/apple/Downloads/Scrapping/chromedriver/chromedriver'

# Setup Chrome options (headless optional)
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment if you want no browser UI

# Setup the Chrome driver service
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Load CSV
df = pd.read_csv('PM DG - Google scholar.csv')  

# Prepare Abstract2 column
df['Abstract2'] = ''

for index, row in df.iterrows():
    url = row['ArticleURL']
    print(f"Processing row {index}: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)  # wait for page to load, adjust as needed
        
        # Get page source
        html = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Try to find the Abstract section
        # This depends on website structure - some examples:
        
        abstract_text = ''
        
        # Common patterns to try:
        # 1. Look for element with id or class containing "abstract"
        abstract_section = soup.find(id='abstract') or soup.find(class_='abstract') or soup.find('section', class_='abstract')
        
        # 2. If not found, try searching for h2 or h3 headers with text "Abstract" and get the next sibling
        if not abstract_section:
            headers = soup.find_all(['h2', 'h3'])
            for header in headers:
                if 'abstract' in header.get_text(strip=True).lower():
                    # Try next sibling or next element with text
                    sibling = header.find_next_sibling()
                    if sibling:
                        abstract_text = sibling.get_text(strip=True)
                    break
        
        if abstract_section:
            abstract_text = abstract_section.get_text(strip=True)
        
        # Save extracted abstract text
        df.at[index, 'Abstract2'] = abstract_text
        
        print(f"Extracted Abstract: {abstract_text[:60]}...")  # print first 60 chars
        
    except Exception as e:
        print(f"Error processing {url}: {e}")
        df.at[index, 'Abstract2'] = ''

# Close the browser
driver.quit()

# Save updated CSV
df.to_csv('yourfile_with_abstract.csv', index=False)
print("Done! Saved to yourfile_with_abstract.csv")

