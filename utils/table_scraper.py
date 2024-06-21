import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    service = ChromeService(executable_path='./chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_page(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    rows = soup.find_all('tr', id='table-content')
    page_data = []
    for row in rows:
        columns = row.find_all('td')
        title = columns[1].find('a').text
        title_url = columns[1].find('a')['href']
        description = columns[2].text.strip()
        regulation_number = columns[3].text.strip()
        sector = columns[4].text.strip()
        sub_sector = columns[5].text.strip()
        regulation_type = columns[6].text.strip()
        year = columns[7].text.strip()
        page_data.append([title, title_url, description, regulation_number,
                          sector, sub_sector, regulation_type, year])
    return page_data


def scrape_all_pages():
    driver = setup_driver()
    driver.get("https://www.ojk.go.id/id/Regulasi/Default.aspx")
    base_url = "https://www.ojk.go.id"
    all_data = []

    all_data.extend(scrape_page(driver))
    print("Page 1 successfully scraped.")

    i = 2
    while True:
        try:
            next_page_text = str(i)
            pagination_container = driver.find_element(
                By.ID, 'ctl00_PlaceHolderMain_ctl00_DataPagerArticles')

            if i % 10 == 1 and i >= 10:
                if i > 11:
                    next_page_link = pagination_container.find_element(
                        By.XPATH, f'//a[@href="javascript:__doPostBack(\'ctl00$PlaceHolderMain$ctl00$DataPagerArticles$ctl01$ctl11\',\'\')"]')
                else:
                    next_page_link = pagination_container.find_element(
                        By.XPATH, f'//a[@href="javascript:__doPostBack(\'ctl00$PlaceHolderMain$ctl00$DataPagerArticles$ctl01$ctl10\',\'\')"]')
            else:
                next_page_link = pagination_container.find_element(
                    By.LINK_TEXT, next_page_text)

            driver.execute_script("arguments[0].click();", next_page_link)

            all_data.extend(scrape_page(driver))
            print(f"Page {i} successfully scraped.")

            i += 1
        except Exception as e:
            print('No more pages to scrape.')
            break

    df = pd.DataFrame(all_data, columns=['Title', 'URL', 'Description',
                      'Regulation Number', 'Sector', 'Sub Sector', 'Regulation Type', 'Year'])

    for index, row in df.iterrows():
        driver.get(base_url + row['URL'])
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        body = soup.find('body')
        if body.text.strip() == '':
            df.at[index, 'notes'] = 'Need to sign in'
        else:
            df.at[index, 'notes'] = 'Success'

        print(f"Checked {index + 1} out of {len(df)} rows.")

    driver.quit()

    # create csv folder if not exists
    if not os.path.exists('./csv'):
        os.makedirs('./csv')

    df.to_csv('./csv/ojk_all_pages.csv', index=False)
    print("Data has been scraped and saved to ojk_all_pages.csv")
