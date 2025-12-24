"""
Scraper module for collecting tourist attractions data in Kazan.
"""
import re
import time
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from django.conf import settings

logger = logging.getLogger(__name__)


class KazanAttractionScraper:
    """Scraper for Kazan tourist attractions."""
    
    def __init__(self, headless: bool = True):
        """Initialize scraper with Selenium driver."""
        self.headless = headless
        self.driver = None
        self.base_urls = [
            'https://www.tripadvisor.ru/Attractions-g298520-Activities-Kazan_Republic_of_Tatarstan.html',
            'https://www.visitkazan.ru/',
        ]
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def _close_driver(self):
        """Close Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def scrape_tripadvisor(self, url: str) -> List[Dict]:
        """Scrape attractions from TripAdvisor."""
        attractions = []
        
        try:
            if not self.driver:
                self._init_driver()
            
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Wait for attractions list to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "attraction_element"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all attraction elements
            attraction_elements = soup.find_all('div', class_='attraction_element')
            
            for element in attraction_elements:
                try:
                    name_elem = element.find('div', class_='listing_title')
                    if not name_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    
                    # Get rating
                    rating_elem = element.find('span', class_='ui_bubble_rating')
                    rating = 0.0
                    if rating_elem:
                        rating_class = rating_elem.get('class', [])
                        for cls in rating_class:
                            if 'bubble_' in cls:
                                rating_str = cls.split('_')[-1]
                                rating = float(rating_str) / 10.0
                    
                    # Get link
                    link_elem = element.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://www.tripadvisor.ru{link}"
                    
                    # Get address (if available)
                    address_elem = element.find('span', class_='format_address')
                    address = address_elem.get_text(strip=True) if address_elem else None
                    
                    attractions.append({
                        'name': name,
                        'rating': rating,
                        'url': link,
                        'address': address,
                        'source': 'tripadvisor'
                    })
                except Exception as e:
                    logger.error(f"Error parsing attraction element: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping TripAdvisor: {e}")
        
        return attractions
    
    def scrape_visitkazan(self, url: str) -> List[Dict]:
        """Scrape attractions from visitkazan.ru."""
        attractions = []
        
        try:
            if not self.driver:
                self._init_driver()
            
            self.driver.get(url)
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find attraction cards (adjust selectors based on actual site structure)
            attraction_cards = soup.find_all('div', class_=re.compile(r'attraction|place|object'))
            
            for card in attraction_cards:
                try:
                    name_elem = card.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name'))
                    if not name_elem:
                        continue
                    
                    name = name_elem.get_text(strip=True)
                    
                    # Get description
                    desc_elem = card.find('p', class_=re.compile(r'description|text'))
                    description = desc_elem.get_text(strip=True) if desc_elem else None
                    
                    # Get link
                    link_elem = card.find('a', href=True)
                    link = link_elem['href'] if link_elem else None
                    if link and not link.startswith('http'):
                        link = f"https://www.visitkazan.ru{link}"
                    
                    attractions.append({
                        'name': name,
                        'description': description,
                        'url': link,
                        'source': 'visitkazan'
                    })
                except Exception as e:
                    logger.error(f"Error parsing attraction card: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping visitkazan.ru: {e}")
        
        return attractions
    
    def get_coordinates_from_address(self, address: str) -> Optional[Dict]:
        """Get coordinates from address (placeholder - would use geocoding API)."""
        # In production, use geocoding API (Yandex Maps, Google Maps, etc.)
        # For now, return None
        return None
    
    def scrape_all(self) -> List[Dict]:
        """Scrape attractions from all sources."""
        all_attractions = []
        
        try:
            self._init_driver()
            
            # Scrape TripAdvisor
            for url in self.base_urls:
                if 'tripadvisor' in url:
                    logger.info(f"Scraping TripAdvisor: {url}")
                    attractions = self.scrape_tripadvisor(url)
                    all_attractions.extend(attractions)
                elif 'visitkazan' in url:
                    logger.info(f"Scraping VisitKazan: {url}")
                    attractions = self.scrape_visitkazan(url)
                    all_attractions.extend(attractions)
        
        finally:
            self._close_driver()
        
        return all_attractions
    
    def enrich_attraction_data(self, attraction_data: Dict) -> Dict:
        """Enrich attraction data with additional information."""
        # Get coordinates if address is available
        if attraction_data.get('address'):
            coords = self.get_coordinates_from_address(attraction_data['address'])
            if coords:
                attraction_data['latitude'] = coords.get('lat')
                attraction_data['longitude'] = coords.get('lng')
        
        # Set default values
        attraction_data.setdefault('rating', 0.0)
        attraction_data.setdefault('visit_duration', 60)
        attraction_data.setdefault('price', 0.0)
        attraction_data.setdefault('is_free', True)
        
        return attraction_data
