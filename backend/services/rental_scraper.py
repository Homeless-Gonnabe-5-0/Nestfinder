from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from datetime import datetime
import time
import re
import os


class RentalScraperService:
    """Service to scrape rental listings using Selenium"""
    
    def __init__(self):
        self.name = "RentalScraperService"
        self.driver = None
    
    def _setup_driver(self, headless=False):
        """Initialize Selenium WebDriver with Chrome"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"[{self.name}] Chrome driver initialized")
    
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print(f"[{self.name}] Chrome driver closed")
    
    def scrape_homestead(self, max_listings=100):
        """
        Scrape Homestead Ottawa apartments
        
        Returns:
            List of apartment dictionaries
        """
        self._setup_driver(headless=False)
        listings = []
        
        url = "https://www.homestead.ca/residential/cities/ottawa"
        
        try:
            print(f"[{self.name}] Scraping Homestead: {url}")
            self.driver.get(url)
            print("  Waiting for page to load...")
            time.sleep(5)
            
            # Scroll to load all listings
            print("  Scrolling to load all listings...")
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # The listings are in: li.property-search-homestead__item
            listing_elements = self.driver.find_elements(By.CSS_SELECTOR, 'li.property-search-homestead__item')
            print(f"  Found {len(listing_elements)} listings")
            
            for idx, element in enumerate(listing_elements[:max_listings]):
                try:
                    # Building name
                    title_elem = element.find_element(By.CSS_SELECTOR, 'h3.listing-card__building-name')
                    title = title_elem.text.strip()
                    
                    # Address
                    address_elem = element.find_element(By.CSS_SELECTOR, 'p.listing-card__address')
                    address = address_elem.text.strip()
                    
                    # URL
                    link_elem = element.find_element(By.CSS_SELECTOR, 'a.hyperlink-default')
                    listing_url = link_elem.get_attribute('href')
                    
                    # Price (Starting from $X)
                    try:
                        price_elem = element.find_element(By.CSS_SELECTOR, 'span.listing-card__rate__min')
                        price = self._clean_price(price_elem.text)
                    except:
                        price = None
                    
                    # Bedrooms
                    try:
                        beds_elem = element.find_element(By.CSS_SELECTOR, 'span.listing-card__beds .listing-card__detail-value')
                        bedrooms_text = beds_elem.text.strip()
                        bedrooms = self._parse_bedrooms(bedrooms_text)
                    except:
                        bedrooms = None
                    
                    # Bathrooms
                    try:
                        baths_elem = element.find_element(By.CSS_SELECTOR, 'span.listing-card__baths .listing-card__detail-value')
                        bathrooms_text = baths_elem.text.strip()
                        bathrooms = self._parse_bathrooms(bathrooms_text)
                    except:
                        bathrooms = 1.0
                    
                    # Image
                    try:
                        img_elem = element.find_element(By.CSS_SELECTOR, 'img.listing-card__photo')
                        image_url = img_elem.get_attribute('src')
                    except:
                        image_url = None
                    
                    apartment = {
                        'id': f"homestead_{hash(listing_url)}",
                        'title': title,
                        'price': price,
                        'address': address,
                        'bedrooms': bedrooms,
                        'bathrooms': bathrooms,
                        'url': listing_url,
                        'image_url': image_url,
                        'neighborhood': self._extract_neighborhood(address),
                        'scraped_at': datetime.now().isoformat(),
                        'source': 'homestead'
                    }
                    
                    listings.append(apartment)
                    print(f"    {idx+1}. {title} - ${price} - {bedrooms}BR - {address[:30]}...")
                
                except Exception as e:
                    print(f"    Error parsing listing {idx+1}: {e}")
                    continue
            
            print(f"\n  Successfully scraped {len(listings)} listings")
        
        except Exception as e:
            print(f"[{self.name}] Error during scraping: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._close_driver()
        
        return listings
    
    def _clean_price(self, price_str):
        """Extract numeric price from string"""
        if not price_str:
            return None
        # Remove $ and commas, then extract all digits
        match = re.search(r'\$?\s*(\d+)', price_str.replace(',', ''))
        if match:
            return int(match.group(1))
        return None
    
    def _parse_bedrooms(self, text):
        """Parse bedrooms - could be '1', '0 - 3', etc."""
        if not text:
            return None
        # If it's a range like "0 - 3", take the minimum
        if '-' in text:
            parts = text.split('-')
            return int(parts[0].strip())
        # If it's a single number
        try:
            return int(text.strip())
        except:
            return None
    
    def _parse_bathrooms(self, text):
        """Parse bathrooms - could be '1', '1 - 2.5', etc."""
        if not text:
            return 1.0
        # If it's a range like "1 - 2.5", take the minimum
        if '-' in text:
            parts = text.split('-')
            return float(parts[0].strip())
        # If it's a single number
        try:
            return float(text.strip())
        except:
            return 1.0
    
    def _extract_neighborhood(self, location_str):
        """Extract Ottawa neighborhood from location string"""
        if not location_str:
            return "Ottawa"
        
        neighborhoods = [
            'Centretown', 'Byward Market', 'ByWard Market', 'Sandy Hill', 'The Glebe',
            'Hintonburg', 'Westboro', 'Old Ottawa South', 'Little Italy',
            'New Edinburgh', 'Vanier', 'Kanata', 'Barrhaven', 'Orleans',
            'Alta Vista', 'Nepean', 'Gloucester', 'Rockcliffe', 'Gatineau',
            'Downtown', 'Market'
        ]
        
        location_lower = location_str.lower()
        for neighborhood in neighborhoods:
            if neighborhood.lower() in location_lower:
                return neighborhood
        
        return "Ottawa"
    
    def scrape_listings(self, source='homestead', max_listings=100, output_file=None):
        """Main scraping method"""
        print(f"\n{'='*60}")
        print(f"[{self.name}] Starting {source} scrape")
        print(f"{'='*60}\n")
        
        if source == 'homestead':
            listings = self.scrape_homestead(max_listings)
        else:
            print(f"Unknown source: {source}")
            return []
        
        if output_file and listings:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(listings, f, indent=2)
            print(f"\n[{self.name}] Saved {len(listings)} listings to {output_file}")
        
        return listings
    
    def get_cached_listings(self, cache_file='cache/homestead_listings.json'):
        """Load cached listings"""
        try:
            with open(cache_file, 'r') as f:
                listings = json.load(f)
            print(f"[{self.name}] Loaded {len(listings)} cached listings")
            return listings
        except FileNotFoundError:
            print(f"[{self.name}] No cache found at {cache_file}")
            return []


if __name__ == "__main__":
    scraper = RentalScraperService()
    
    listings = scraper.scrape_listings(
        source='homestead',
        max_listings=30,
        output_file='cache/homestead_listings.json'
    )
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total listings scraped: {len(listings)}")
    
    if listings:
        print(f"\nFirst 3 listings:")
        for i, listing in enumerate(listings[:3]):
            print(f"\n{i+1}. {listing['title']}")
            print(f"   Price: ${listing.get('price', 'N/A')}")
            print(f"   Bedrooms: {listing.get('bedrooms', 'N/A')}")
            print(f"   Address: {listing['address']}")
            print(f"   URL: {listing['url']}")