#!/usr/bin/env python3
import os
import re
import json
import time
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kostats_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("kostats_scraper")

# Configuration
BASE_URL = "http://www.kostats.com"
LOGIN_URL = "http://www.kostats.com/amember5/member"
BASE_DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
HISTORY_FILE = os.path.join(BASE_DOWNLOAD_DIR, "download_history.json")

# Sport subscription pages
SPORT_PAGES = {
    "CBK": "http://www.kostats.com/CBK_Subscription/CBK.HTM",
    "CFB": "http://www.kostats.com/CFB_Subscription/CFB.HTM",
    "MLB": "http://www.kostats.com/MLB_Subscription/MLB.HTM",
    "NBA": "http://www.kostats.com/NBA_Subscription/NBA.HTM",
    "NFL": "http://www.kostats.com/NFL_Subscription/NFL.HTM",
    "NHL": "http://www.kostats.com/NHL_Subscription/NHL.HTM"
}

# Get credentials from environment variables
USERNAME = os.getenv("KOSTATS_USERNAME")
PASSWORD = os.getenv("KOSTATS_PASSWORD")

class KOStatsScraper:
    def __init__(self):
        # Validate credentials
        if not USERNAME or not PASSWORD:
            raise ValueError("Missing credentials. Set KOSTATS_USERNAME and KOSTATS_PASSWORD in .env file")
            
        self.session = requests.Session()
        
        # Create base download directory if it doesn't exist
        if not os.path.exists(BASE_DOWNLOAD_DIR):
            os.makedirs(BASE_DOWNLOAD_DIR)
            
        # Load download history after ensuring the directory exists
        self.download_history = self._load_download_history()
        
        # Create sport-specific directories
        for sport in SPORT_PAGES.keys():
            sport_dir = os.path.join(BASE_DOWNLOAD_DIR, sport)
            if not os.path.exists(sport_dir):
                os.makedirs(sport_dir)
    
    def _load_download_history(self):
        """Load the download history from file"""
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.error("Error reading history file, starting fresh")
                    return {}
        return {}
    
    def _save_download_history(self):
        """Save the download history to file"""
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.download_history, f, indent=2)
    
    def login(self):
        """Log in to the KOStats website"""
        logger.info("Logging in to KOStats")
        
        # First get the login page to capture any cookies/tokens
        login_page = self.session.get(LOGIN_URL)
        
        # Find the login form
        soup = BeautifulSoup(login_page.text, 'html.parser')
        form = soup.find('form', {'id': 'am-login-form'}) or soup.find('form', {'action': re.compile(r'login')})
        
        if not form:
            logger.error("Could not find login form")
            return False
        
        # Extract form action and hidden fields
        action = form.get('action') or LOGIN_URL
        if not action.startswith('http'):
            action = urljoin(BASE_URL, action)
        
        # Extract all form inputs including hidden fields
        form_data = {}
        for input_field in form.find_all('input'):
            if input_field.get('name'):
                form_data[input_field.get('name')] = input_field.get('value', '')
        
        # Add credentials
        form_data['amember_login'] = USERNAME
        form_data['amember_pass'] = PASSWORD
        
        # Submit the login form
        response = self.session.post(action, data=form_data)
        
        # Check if login was successful (look for typical success indicators)
        if "logout" in response.text.lower() or "my account" in response.text.lower():
            logger.info("Login successful")
            return True
        else:
            logger.error("Login failed")
            return False
    
    def get_file_links(self, sport_code):
        """Get all file links from a sport page"""
        sport_url = SPORT_PAGES.get(sport_code)
        if not sport_url:
            logger.error(f"Unknown sport code: {sport_code}")
            return []
        
        logger.info(f"Getting file links for {sport_code}")
        response = self.session.get(sport_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to access {sport_url}, status code: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Find all links ending with .TXT in the table
        for link in soup.find_all('a', href=re.compile(r'\.TXT$', re.IGNORECASE)):
            file_url = urljoin(sport_url, link['href'])
            file_name = os.path.basename(file_url)
            links.append((file_name, file_url))
        
        logger.info(f"Found {len(links)} files for {sport_code}")
        return links
    
    def download_file(self, sport_code, file_name, file_url):
        """Download a file if it hasn't been downloaded before"""
        # Check if file was already downloaded
        if sport_code in self.download_history and file_name in self.download_history[sport_code]:
            logger.info(f"Skipping {file_name} - already downloaded")
            return False
        
        # Download the file
        logger.info(f"Downloading {file_name}")
        response = self.session.get(file_url)
        
        if response.status_code != 200:
            logger.error(f"Failed to download {file_url}, status code: {response.status_code}")
            return False
        
        # Save the file to sport-specific directory
        file_path = os.path.join(BASE_DOWNLOAD_DIR, sport_code, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        # Update download history
        if sport_code not in self.download_history:
            self.download_history[sport_code] = {}
        
        self.download_history[sport_code][file_name] = {
            "downloaded_at": datetime.now().isoformat(),
            "url": file_url
        }
        
        logger.info(f"Successfully downloaded {file_name}")
        return True
    
    def process_sport(self, sport_code):
        """Process all files for a sport"""
        file_links = self.get_file_links(sport_code)
        downloaded_count = 0
        
        for file_name, file_url in file_links:
            if self.download_file(sport_code, file_name, file_url):
                downloaded_count += 1
            
            # Be nice to the server
            time.sleep(1)
        
        logger.info(f"Downloaded {downloaded_count} new files for {sport_code}")
        return downloaded_count
    
    def run(self):
        """Run the scraper for all sports"""
        if not self.login():
            logger.error("Login failed, aborting")
            return
        
        total_downloaded = 0
        for sport_code in SPORT_PAGES.keys():
            total_downloaded += self.process_sport(sport_code)
        
        self._save_download_history()
        logger.info(f"Scraper completed. Downloaded {total_downloaded} new files in total.")

if __name__ == "__main__":
    logger.info("Starting KOStats scraper")
    scraper = KOStatsScraper()
    scraper.run()