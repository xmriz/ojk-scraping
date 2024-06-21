import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    service = ChromeService(executable_path='./chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def sanitize_filename(filename):
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return sanitized[:255]


def download_pdf(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False


def download_pdfs(df):
    driver = setup_driver()
    base_url = "https://www.ojk.go.id"
    paths = df[df['notes'] == 'Success']['URL'].tolist()
    pdf_data = []
    download_dir = './data'

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    for index, path in enumerate(paths):
        driver.get(base_url + path)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title = soup.find('h1', class_='title-in').text.strip()
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))

        for link in pdf_links:
            filename = link.text.strip()
            altlink = link['href']
            full_url = base_url + altlink

            if filename:
                sanitized_filename = sanitize_filename(filename)
                pdf_path = os.path.join(download_dir, sanitized_filename)
                success = download_pdf(full_url, pdf_path)
                if not success:
                    retry_count = 3
                    for attempt in range(retry_count):
                        print(
                            f"Retrying {full_url} (Attempt {attempt + 1}/{retry_count})")
                        success = download_pdf(full_url, pdf_path)
                        if success:
                            break

                pdf_data.append([title, filename, full_url])

        print(f"Scraped {index + 1} out of {len(paths)} rows")

    pdf_df = pd.DataFrame(pdf_data, columns=['title', 'filename', 'altlink'])
    pdf_df.to_csv('./csv/ojk_pdf_data.csv', index=False)
    print("PDF data has been scraped, downloaded, and saved to ojk_pdf_data.csv")
    driver.quit()
