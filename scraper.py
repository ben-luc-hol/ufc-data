import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
from tqdm import tqdm

class FighterScraper(object):
    def __init__(self):
        self.base_url = "http://ufcstats.com/statistics/fighters"

    def get_links(self, url):

        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve page for URL: {url}")
            return []
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find all links to fighter profiles
        fighter_links = soup.select('td.b-statistics__table-col a.b-link.b-link_style_black')
        # Extract and return the href attributes (URLs)
        return [link['href'] for link in fighter_links]

    def scrape_fighter_urls(self):
        alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        all_fighter_links = []
        for char in alphabet:
            index_url = f"{self.base_url}?char={char}&page=all"
            print(f"Scraping fighters for letter: {char}")
            links = self.get_links(index_url)
            if links:
                all_fighter_links.extend(links)
            else:
                print(f"No fighters found for letter: {char}")
        return all_fighter_links

    def get_fighter_info(self, fighter_link):
        response = requests.get(fighter_link)
        if response.status_code != 200:
            print(f"Failed to retrieve page for URL: {fighter_link}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        fighter_info = {}

        # Fighter name
        name_elem = soup.select_one('.b-content__title-highlight')
        fighter_info['name'] = name_elem.text.strip() if name_elem else None

        # Basic info (height, weight, reach, stance, DOB)
        info_box = soup.select_one('.b-list__info-box_style_small-width')
        if info_box:
            for item in info_box.select('.b-list__box-list-item'):
                label = item.select_one('.b-list__box-item-title')
                value = item.contents[-1].strip()
                if label:
                    key = label.text.strip().rstrip(':').lower()
                    fighter_info[key] = value

        # Career statistics
        stats_box = soup.select_one('.b-list__info-box_style_middle-width')
        if stats_box:
            for item in stats_box.select('.b-list__box-list-item'):
                label = item.select_one('.b-list__box-item-title')
                value = item.contents[-1].strip()
                if label:
                    key = label.text.strip().rstrip(':').lower()
                    fighter_info[key] = value

        # Clean up some fields
        fighter_info['height'] = fighter_info.get('height', '').replace('"', '')
        fighter_info['weight'] = fighter_info.get('weight', '').replace(' lbs.', '')

        if 'dob' in fighter_info:
            fighter_info['dob'] = fighter_info['dob'].strip()

        # Convert percentages to floats
        for key in ['str. acc', 'str. def', 'td acc', 'td def']:
            if key in fighter_info:
                fighter_info[key] = float(fighter_info[key].strip('%')) / 100

        # Convert string numbers to floats
        for key in ['slpm', 'sapm', 'td avg', 'sub. avg']:
            if key in fighter_info:
                fighter_info[key] = float(fighter_info[key])

        return fighter_info

    def get_dataset(self):
        # First, get all fighter URLs
        fighter_urls = self.scrape_fighter_urls()

        # Initialize an empty list to store fighter data
        fighters_data = []

        # Use tqdm for a progress bar
        for url in tqdm(fighter_urls, desc="Scraping fighter data"):
            fighter_info = self.get_fighter_info(url)
            if fighter_info:
                fighters_data.append(fighter_info)

            # Add a small delay to be respectful to the server
            time.sleep(0.5)

        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(fighters_data)

        # Reorder columns for better readability
        column_order = [
            'name', 'height', 'weight', 'reach', 'stance', 'dob',
            'slpm', 'str. acc', 'sapm', 'str. def',
            'td avg', 'td acc', 'td def', 'sub. avg'
        ]

        # Only include columns that exist in the DataFrame
        column_order = [col for col in column_order if col in df.columns]

        # Add any remaining columns to the end
        for col in df.columns:
            if col not in column_order:
                column_order.append(col)

        df = df[column_order]

        return df


        # fighter name
        # fighter height
        # fighter weight
        # fighter reach
        # fighter DOB
        #SLpM
        #Str.Acc
        #SApM:
        #Str. Def
        #TD Avg.
        #TD Acc.
        #TD Def.
        #Sub. Avg.


        # """
        # for documentation only:
        #
        #
        # SLpM - Significant Strikes Landed per Minute
        #
        # Str. Acc. - Significant Striking Accuracy
        #
        # SApM - Significant Strikes Absorbed per Minute
        #
        # Str. Def. - Significant Strike Defence (the % of opponents strikes that did not land)
        #
        # TD Avg. - Average Takedowns Landed per 15 minutes
        #
        # TD Acc. - Takedown Accuracy
        #
        # TD Def. - Takedown Defense (the % of opponents TD attempts that did not land)
        #
        # Sub. Avg. - Average Submissions Attempted per 15 minutes
        # """
        #
