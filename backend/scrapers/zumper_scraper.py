import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

YELLOWCAKE_API_URL = "https://api.yellowcake.dev/v1/extract-stream"
YELLOWCAKE_API_KEY = os.getenv("YELLOWCAKE_API_KEY")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scraped")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "zumper.json")

CONFIG = {
    "name": "zumper",
    "url": "https://www.zumper.com/apartments-for-rent/ottawa-on",
    "prompt": """Get all apartment listings. For each one extract:
- building_name
- monthly_rent
- full_address
- bedrooms
- bathrooms
- sqft
- amenities (parking, gym, pool, laundry, etc)
- utilities_included (heat, hydro, water, internet, cable)
- appliances (fridge, stove, dishwasher, washer, dryer, AC)
- pet_policy (cats, dogs, no pets)
- lease_terms (month-to-month, 1 year, etc)
- move_in_date
- listing_url"""
}


def scrape():
    print(f"[ZUMPER] Starting scrape...")
    print(f"[ZUMPER] URL: {CONFIG['url']}")
    
    if not YELLOWCAKE_API_KEY:
        print("[ZUMPER] ERROR: No YELLOWCAKE_API_KEY set")
        return []
    
    payload = {
        "url": CONFIG["url"],
        "prompt": CONFIG["prompt"]
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
                            if any(k in data for k in ['apartment_name', 'building_name', 'rent', 'address', 'url']):
                                listings.append(data)
                    except:
                        pass
                elif text.startswith('data:') and 'success' in text:
                    data = json.loads(text[5:].strip())
                    if data.get("success") and data.get("data"):
                        listings.extend(data.get("data", []))
                    print(f"[ZUMPER] Got {len(listings)} listings")
                    break
                elif 'error' in text.lower() and 'data:' in text and 'ERROR' in text:
                    print(f"[ZUMPER] API Error: {text}")
                    break
        
        if listings:
            save_results(listings)
        
        return listings
        
    except Exception as e:
        print(f"[ZUMPER] Error: {e}")
        return []


def save_results(listings):
    output = {
        "source": "zumper",
        "scraped_at": datetime.now().isoformat(),
        "url": CONFIG["url"],
        "count": len(listings),
        "listings": listings
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[ZUMPER] Saved {len(listings)} listings to {OUTPUT_FILE}")


if __name__ == "__main__":
    results = scrape()
    
    if results:
        print(f"\n[ZUMPER] Sample listing:")
        print(json.dumps(results[0], indent=2))
    else:
        print("[ZUMPER] No results")
