import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from PIL import Image
import pytesseract
import io
import os
import creds

import openai  # <-- Correct import for openai 0.28

# Set your OpenAI API key here or via environment variable
# openai.api_key = os.getenv("OPENAI_API_KEY") or "your-api-key-here"

openai.api_key = cred.api_key  # Replace with your actual API key or use environment variable)

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

# Prepare Abstract2 column if it doesn't exist
if 'Abstract2' not in df.columns:
    df['Abstract2'] = ''

# Function to call GPT-4 with OpenAI ChatCompletion API
def extract_abstract_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo",  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an assistant that extracts abstracts from scientific papers."},
                {"role": "user", "content": f"Extract the abstract from the following text:\n\n{text}"}
            ],
            max_tokens=300,
            temperature=0.2,
            n=1
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"GPT extraction failed: {e}")
        return ''

# Process only rows 105 to 109 (index 104 to 108)
for index in range(110, 115):
    url = df.at[index, 'ArticleURL']
    print(f"Processing row {index + 1}: {url}")
    
    try:
        driver.get(url)
        time.sleep(10)  # wait for page to load, adjust as needed
        
        # Get page source
        html = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        abstract_text = ''
        
        # Try HTML extraction patterns
        abstract_section = soup.find(id='abstract') or soup.find(class_='abstract') or soup.find('section', class_='abstract')
        if abstract_section:
            abstract_text = abstract_section.get_text(strip=True)
        else:
            # Check headers for 'abstract'
            headers = soup.find_all(['h2', 'h3'])
            for header in headers:
                if 'abstract' in header.get_text(strip=True).lower():
                    sibling = header.find_next_sibling()
                    if sibling:
                        abstract_text = sibling.get_text(strip=True)
                    break
        
        # If HTML extraction failed or empty, do OCR + GPT fallback
        if not abstract_text.strip():
            # Screenshot the page (viewport only)
            screenshot_png = driver.get_screenshot_as_png()
            
            # Convert PNG bytes to PIL Image
            image = Image.open(io.BytesIO(screenshot_png))
            
            # OCR with pytesseract
            ocr_text = pytesseract.image_to_string(image)
            
            # Use GPT to extract abstract from OCR text
            abstract_text = extract_abstract_with_gpt(ocr_text)
        
        # Save extracted abstract text
        df.at[index, 'Abstract2'] = abstract_text
        
        print(f"Abstract: {abstract_text[:60]}...")  # print first 60 chars
        
    except Exception as e:
        print(f"Error processing {url}: {e}")
        df.at[index, 'Abstract2'] = ''

# Close the browser
driver.quit()

# Save updated CSV
df.to_csv('yourfile_with_abstract.csv', index=False)
print("Done! Saved to yourfile_with_abstract.csv")

