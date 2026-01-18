import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

YELLOWCAKE_API_URL = "https://api.yellowcake.dev/v1/extract-stream"
YELLOWCAKE_API_KEY = os.getenv("YELLOWCAKE_API_KEY")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "kijiji.json")

# Target number of listings
TARGET_LISTINGS = 1000
MAX_PAGES = 30  # Safety limit

BASE_URL = "https://www.kijiji.ca/b-apartments-condos/ottawa"
CATEGORY = "c37l1700185"

PROMPT = """Get all rental listings. For each one extract:
- listing_title
- monthly_rent
- location
- bedrooms
- bathrooms
- sqft
- description
- utilities_included (heat, hydro, water, internet, cable - what is included)
- appliances (fridge, stove, dishwasher, washer, dryer, AC, microwave)
- pet_policy (cats allowed, dogs allowed, no pets)
- parking (included, extra cost, none)
- laundry (in-unit, shared, coin-op)
- lease_terms
- move_in_date
- listing_url"""


def get_page_url(page_num):
    """Generate URL for a specific page number."""
    if page_num == 1:
        return f"{BASE_URL}/{CATEGORY}"
    return f"{BASE_URL}/page-{page_num}/{CATEGORY}"


def scrape_page(url):
    """Scrape a single page and return listings."""
    if not YELLOWCAKE_API_KEY:
        print("[KIJIJI] ERROR: No YELLOWCAKE_API_KEY set")
        return []
    
    payload = {
        "url": url,
        "prompt": PROMPT
    }
    
    headers = {
        "X-API-Key": YELLOWCAKE_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            YELLOWCAKE_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=300
        )
        
        listings = []
        
        for line in response.iter_lines():
            if line:
                text = line.decode('utf-8')
                
                if text.startswith('event:'):
                    continue
                elif text.startswith('data:'):
                    try:
                        data = json.loads(text[5:].strip())
                        if isinstance(data, dict) and 'schema' not in data and 'stage' not in data and 'message' not in data:
                            if any(k in data for k in ['listing_title', 'monthly_rent', 'location', 'bedrooms', 'listing_url']):
                                listings.append(data)
                    except:
                        pass
                elif text.startswith('data:') and 'success' in text:
                    data = json.loads(text[5:].strip())
                    if data.get("success") and data.get("data"):
                        listings.extend(data.get("data", []))
                    break
                elif 'error' in text.lower() and 'data:' in text and 'ERROR' in text:
                    print(f"[KIJIJI] API Error: {text}")
                    break
        
        return listings
        
    except Exception as e:
        print(f"[KIJIJI] Error scraping page: {e}")
        return []


def scrape():
    """Scrape multiple pages until we reach target listings."""
    print(f"[KIJIJI] Starting scrape - Target: {TARGET_LISTINGS} listings")
    
    all_listings = []
    seen_urls = set()  # Track unique listings by URL
    
    for page in range(1, MAX_PAGES + 1):
        url = get_page_url(page)
        print(f"[KIJIJI] Scraping page {page}: {url}")
        
        page_listings = scrape_page(url)
        
        if not page_listings:
            print(f"[KIJIJI] No listings on page {page}, stopping.")
            break
        
        # Deduplicate by listing URL
        new_count = 0
        for listing in page_listings:
            listing_url = listing.get('listing_url', '')
            if listing_url and listing_url not in seen_urls:
                seen_urls.add(listing_url)
                all_listings.append(listing)
                new_count += 1
        
        print(f"[KIJIJI] Page {page}: {new_count} new listings (Total: {len(all_listings)})")
        
        if len(all_listings) >= TARGET_LISTINGS:
            print(f"[KIJIJI] Reached target of {TARGET_LISTINGS} listings!")
            break
        
        # Be nice to the API
        time.sleep(2)
    
    if all_listings:
        save_results(all_listings)
    
    return all_listings


def save_results(listings):
    output = {
        "source": "kijiji",
        "scraped_at": datetime.now().isoformat(),
        "pages_scraped": "multiple",
        "count": len(listings),
        "listings": listings
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[KIJIJI] Saved {len(listings)} listings to {OUTPUT_FILE}")


if __name__ == "__main__":
    results = scrape()
    
    if results:
        print(f"\n[KIJIJI] Total: {len(results)} listings")
        print(f"[KIJIJI] Sample listing:")
        print(json.dumps(results[0], indent=2))
    else:
        print("[KIJIJI] No results")
