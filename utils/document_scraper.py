import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse

from utils.setup_driver import setup_driver


def sanitize_href_filename(filename):
    decoded_filename = urllib.parse.unquote(filename)
    sanitized = ' '.join(decoded_filename.split())
    return sanitized


def download_document(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False


def download_documents(df):
    driver = setup_driver()
    base_url = "https://www.ojk.go.id"
    paths = df[df['status'] == 'Success']['URL'].tolist()
    document_data = []
    download_dir = './data'

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    for index, path in enumerate(paths):
        driver.get(base_url + path)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title = soup.find('h1', class_='title-in').text.strip()
        sektor = soup.find(
            'span', class_='sektor-regulasi-display').text.strip()
        subsektor = soup.find(
            'span', class_='subsektor-regulasi-display').text.strip()
        jenis_regulasi = soup.find(
            'span', class_='jenis-regulasi-display').text.strip()
        nomor_regulasi = soup.find(
            'span', class_='nomor-regulasi-display').text.strip()
        nomor_regulasi = soup.find(
            'span', class_='display-date-text').text.strip()
        document_links_div = soup.find(
            'div', id='ctl00_PlaceHolderMain_ctl02__ControlWrapper_RichHtmlField')
        document_links = document_links_div.find_all('a')

        for link in document_links:
            if 'href' in link.attrs:
                filename = sanitize_href_filename(link['href'].split('/')[-1])
                checked_text_value = link.text.strip()
                altlink = link['href']
                full_url = base_url + altlink

                if checked_text_value:
                    document_path = os.path.join(download_dir, filename)
                    success = download_document(full_url, document_path)
                    if not success:
                        retry_count = 3
                        for attempt in range(retry_count):
                            print(
                                f"Retrying {full_url} (Attempt {attempt + 1}/{retry_count})")
                            success = download_document(
                                full_url, document_path)
                            if success:
                                break

                    document_data.append(
                        [title, sektor, subsektor, jenis_regulasi, nomor_regulasi, filename, full_url])

        print(f"Scraped {index + 1} out of {len(paths)} rows")

    document_df = pd.DataFrame(document_data, columns=[
                               'title', 'sektor', 'subsektor', 'jenis_regulasi', 'nomor_regulasi', 'filename', 'url'])
    document_df.to_csv('./csv/ojk_document_data.csv', index=False)
    print("document data has been scraped, downloaded, and saved to ojk_document_data.csv")
    driver.quit()
