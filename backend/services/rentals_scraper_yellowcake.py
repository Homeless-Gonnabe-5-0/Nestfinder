import requests
import json
from datetime import datetime
import os
import re


class RentalScraperService:
    """Service to scrape rental listings using Yellowcake API"""
    
    def __init__(self, api_key):
        self.name = "RentalScraperService"
        self.api_key = api_key
        self.base_url = "https://api.yellowcake.dev/v1/extract-stream"
    
    def _extract_with_yellowcake(self, url, prompt):
        """
        Extract data from URL using Yellowcake API
        
        Args:
            url: Target URL to scrape
            prompt: Description of content to extract
            
        Returns:
            Extracted data as dict or None if failed
        """
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        
        payload = {
            "url": url,
            "prompt": prompt
        }
        
        print(f"[{self.name}] Sending request to Yellowcake...")
        print(f"  URL: {url}")
        print(f"  Prompt: {prompt}")
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                stream=True
            )
            
            # Process SSE stream
            complete_data = None
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('event: complete'):
                        # Next line should contain the data
                        continue
                    elif line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        try:
                            complete_data = json.loads(data_str)
                            if complete_data.get('success'):
                                print(f"  ✓ Successfully extracted {complete_data.get('metadata', {}).get('itemCount', 0)} items")
                                print(f"  Duration: {complete_data.get('metadata', {}).get('duration', 0) / 1000:.1f}s")
                                return complete_data
                        except json.JSONDecodeError:
                            continue
            
            return complete_data
            
        except Exception as e:
            print(f"[{self.name}] Error during Yellowcake extraction: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def scrape_homestead(self, max_listings=100):
        """
        Scrape Homestead Ottawa apartments using Yellowcake
        
        Returns:
            List of apartment dictionaries
        """
        url = "https://www.homestead.ca/residential/cities/ottawa"
        
        # Craft a detailed prompt for Yellowcake
        prompt = f"""Extract up to {max_listings} rental apartment listings from this page. 
        For each listing, include:
        - building_name: The name of the building
        - address: Full street address
        - price: Monthly rental price (numeric value only, no $ or commas)
        - bedrooms: Number of bedrooms (numeric)
        - bathrooms: Number of bathrooms (numeric)
        - url: Direct link to the listing
        - image_url: URL of the property image
        
        Return all available listings on the page."""
        
        result = self._extract_with_yellowcake(url, prompt)
        
        if not result or not result.get('success'):
            print(f"[{self.name}] Failed to extract data from Yellowcake")
            return []
        
        raw_data = result.get('data', [])
        listings = []
        
        print(f"\n[{self.name}] Processing {len(raw_data)} raw listings...")
        
        for idx, item in enumerate(raw_data[:max_listings]):
            try:
                # Extract and clean the data
                title = item.get('building_name', '').strip()
                address = item.get('address', '').strip()
                listing_url = item.get('url', '').strip()
                
                # Clean price - extract numeric value
                price_raw = item.get('price')
                price = self._clean_price(price_raw)
                
                # Parse bedrooms
                bedrooms_raw = item.get('bedrooms')
                bedrooms = self._parse_number(bedrooms_raw)
                
                # Parse bathrooms
                bathrooms_raw = item.get('bathrooms')
                bathrooms = self._parse_number(bathrooms_raw, default=1.0, as_float=True)
                
                image_url = item.get('image_url', '').strip() or None
                
                apartment = {
                    'id': f"homestead_{hash(listing_url) if listing_url else hash(title)}",
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
                print(f"  {idx+1}. {title} - ${price} - {bedrooms}BR - {address[:30]}...")
            
            except Exception as e:
                print(f"  Error processing listing {idx+1}: {e}")
                continue
        
        print(f"\n[{self.name}] Successfully processed {len(listings)} listings")
        return listings
    
    def _clean_price(self, price_value):
        """Extract numeric price from various formats"""
        if price_value is None:
            return None
        
        # If already a number
        if isinstance(price_value, (int, float)):
            return int(price_value)
        
        # If string, clean it
        price_str = str(price_value)
        # Remove $, commas, and spaces, then extract all digits
        match = re.search(r'\d+', price_str.replace(',', '').replace('$', '').replace(' ', ''))
        if match:
            return int(match.group(0))
        
        return None
    
    def _parse_number(self, value, default=None, as_float=False):
        """Parse a number from various formats"""
        if value is None:
            return default
        
        # If already a number
        if isinstance(value, (int, float)):
            return float(value) if as_float else int(value)
        
        # If string, try to parse
        value_str = str(value).strip()
        
        # Handle ranges like "1 - 2" - take the first number
        if '-' in value_str:
            parts = value_str.split('-')
            value_str = parts[0].strip()
        
        # Extract number
        try:
            if as_float:
                return float(value_str)
            else:
                return int(float(value_str))  # Handle "1.0" -> 1
        except (ValueError, TypeError):
            return default
    
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
        print(f"[{self.name}] Starting {source} scrape with Yellowcake")
        print(f"{'='*60}\n")
        
        if source == 'homestead':
            listings = self.scrape_homestead(max_listings)
        else:
            print(f"Unknown source: {source}")
            return []
        
        if output_file and listings:
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
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
    # Get API key from environment variable or replace with your key
    api_key = os.getenv('YELLOWCAKE_API_KEY', 'YOUR-YELLOWCAKE-API-KEY')
    
    if api_key == 'YOUR-YELLOWCAKE-API-KEY':
        print("⚠️  Please set your Yellowcake API key!")
        print("   Option 1: Set environment variable: export YELLOWCAKE_API_KEY='your-key'")
        print("   Option 2: Replace 'YOUR-YELLOWCAKE-API-KEY' in the code")
        exit(1)
    
    scraper = RentalScraperService(api_key=api_key)
    
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
