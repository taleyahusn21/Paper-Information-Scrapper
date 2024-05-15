import requests
import urllib
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd

def scrape_and_store_links(start_url, target_count):
    # Function to extract URLs and titles from a single page
    def extract_links_from_page(page_html):
        doc = BeautifulSoup(page_html, 'html.parser')
        link_elements = doc.find_all('a', class_='app-card-open__link')
        links = []
        for link_element in link_elements:
            base_url = "https://link.springer.com"
            relative_url = link_element['href']
            url = urllib.parse.urljoin(base_url, relative_url)
            title = link_element.find('span').text.strip()
            links.append((url, title))
        return links

    # Function to scrape multiple pages until reaching the desired count of links
    def scrape_pages(start_url, target_count):
        all_links = []
        current_url = start_url
        while len(all_links) < target_count:
            response = requests.get(current_url)
            if response.status_code == 200:
                page_links = extract_links_from_page(response.text)
                all_links.extend(page_links)
                next_page_link = find_next_page_link(response.text)
                if next_page_link:
                    current_url = next_page_link
                else:
                    break
            else:
                print("Failed to fetch page:", current_url)
                break
        return all_links

    def find_next_page_link(page_html):
        doc = BeautifulSoup(page_html, 'html.parser')
        next_page_element = doc.select_one('a.eds-c-pagination__link[rel="next"]')
        if next_page_element:
            base_url = "https://link.springer.com"
            next_page_url = base_url + next_page_element['href']
            return next_page_url
        else:
            return None

    # Scrape pages until reaching the desired count of links
    all_links = scrape_pages(start_url, target_count)

    # Convert the list of tuples to a DataFrame
    df = pd.DataFrame(all_links, columns=['URL', 'Title'])

    return df
