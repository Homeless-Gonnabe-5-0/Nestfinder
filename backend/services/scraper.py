import os
import json
import re
import requests
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

YELLOWCAKE_API_URL = "https://api.yellowcake.dev/v1/extract-stream"
YELLOWCAKE_API_KEY = os.getenv("YELLOWCAKE_API_KEY")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
CACHE_EXPIRY_HOURS = 24

SOURCES_DIR = os.path.join(os.path.dirname(__file__), "sources")


def load_source_config(source_name: str) -> Optional[Dict]:
    """Load a single source configuration"""
    source_path = os.path.join(SOURCES_DIR, f"{source_name}.json")
    if not os.path.exists(source_path):
        return None
    with open(source_path, 'r') as f:
        return json.load(f)


def get_enabled_sources() -> List[Dict]:
    """Get list of enabled listing sources from individual files"""
    sources = []
    if not os.path.exists(SOURCES_DIR):
        return sources
    
    for filename in os.listdir(SOURCES_DIR):
        if filename.endswith('.json'):
            source_path = os.path.join(SOURCES_DIR, filename)
            with open(source_path, 'r') as f:
                source = json.load(f)
                if source.get('enabled', True):
                    sources.append(source)
    
    return sources


def _get_cache_key(source_name: str, city: str, budget_min: int, budget_max: int, bedrooms: int) -> str:
    """Generate cache key based on source and search parameters"""
    params = f"{source_name}_{city}_{budget_min}_{budget_max}_{bedrooms}"
    return hashlib.md5(params.encode()).hexdigest()


def _get_cache_path(source_name: str, cache_key: str) -> str:
    """Get full path to cache file"""
    source_dir = os.path.join(CACHE_DIR, source_name)
    os.makedirs(source_dir, exist_ok=True)
    return os.path.join(source_dir, f"{cache_key}.json")


def _load_from_cache(source_name: str, city: str, budget_min: int, budget_max: int, bedrooms: int) -> Optional[List[Dict]]:
    """Load cached listings if available and fresh"""
    cache_key = _get_cache_key(source_name, city, budget_min, budget_max, bedrooms)
    cache_path = _get_cache_path(source_name, cache_key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        cached_at = datetime.fromisoformat(cache_data['cached_at'])
        expiry_time = cached_at + timedelta(hours=CACHE_EXPIRY_HOURS)
        
        if datetime.now() < expiry_time:
            hours_ago = (datetime.now() - cached_at).seconds // 3600
            print(f"    [{source_name}] Using cache from {hours_ago}h ago")
            return cache_data['listings']
        else:
            print(f"    [{source_name}] Cache expired")
            return None
    except Exception as e:
        print(f"    [{source_name}] Cache load error: {e}")
        return None


def _save_to_cache(source_name: str, city: str, budget_min: int, budget_max: int, bedrooms: int, listings: List[Dict]):
    """Save listings to cache"""
    cache_key = _get_cache_key(source_name, city, budget_min, budget_max, bedrooms)
    cache_path = _get_cache_path(source_name, cache_key)
    
    cache_data = {
        'source': source_name,
        'cached_at': datetime.now().isoformat(),
        'city': city,
        'budget_min': budget_min,
        'budget_max': budget_max,
        'bedrooms': bedrooms,
        'listings': listings
    }
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"    [{source_name}] Saved {len(listings)} to cache")
    except Exception as e:
        print(f"     [{source_name}] Cache save error: {e}")


def fetch_from_source(source_config: Dict, city: str, max_results: int = 20) -> List[Dict]:
    """Fetch raw listings from a specific source using Yellowcake"""
    
    source_name = source_config['name']
    
    if not YELLOWCAKE_API_KEY:
        print(f"    [{source_name}] No YELLOWCAKE_API_KEY")
        return []

    url_template = source_config['url_template']
    prompt_template = source_config['prompt_template']
    
    target_url = url_template.format(city=city.lower())
    prompt = prompt_template.format(max_results=max_results)
    
    headers = {
        "X-API-Key": YELLOWCAKE_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": target_url,
        "prompt": prompt
    }

    try:
        print(f"    [{source_name}] Scraping {target_url}")
        
        response = requests.post(
            YELLOWCAKE_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        all_listings = []
        event_type = None
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                
                if line_text.startswith('event:'):
                    event_type = line_text.split(':', 1)[1].strip()
                    continue
                elif line_text.startswith('data:'):
                    try:
                        json_data = line_text[5:].strip()
                        
                        if not json_data or json_data == '{}':
                            continue
                        
                        data = json.loads(json_data)
                        
                        if event_type == 'complete':
                            if data.get("success"):
                                final_listings = data.get("data", [])
                                print(f"    [{source_name}] Got {len(final_listings)} listings")
                                return final_listings
                        elif event_type == 'chunk':
                            chunk_listings = data.get("data", [])
                            if chunk_listings:
                                all_listings.extend(chunk_listings)
                        elif event_type == 'error':
                            print(f"    [{source_name}] API error: {data.get('message')}")
                            return []
                    except json.JSONDecodeError:
                        continue
        
        if all_listings:
            print(f"    [{source_name}] Got {len(all_listings)} listings from chunks")
            return all_listings
        else:
            print(f"    [{source_name}] No listings returned")
            return []
        
    except requests.exceptions.RequestException as e:
        print(f"    [{source_name}] Request error: {e}")
        return []
    except Exception as e:
        print(f"    [{source_name}] Unexpected error: {e}")
        return []


def normalize_listing(raw_listing: Dict, source_config: Dict) -> Optional[Dict]:
    """Convert raw listing to standardized format using field mapping"""
    
    field_mapping = source_config['field_mapping']
    
    try:
        normalized = {}
        
        for standard_field, source_field in field_mapping.items():
            normalized[standard_field] = raw_listing.get(source_field, "")
        
        return normalized
    except Exception as e:
        print(f"    Error normalizing listing: {e}")
        return None


def clean_listing(normalized_listing: Dict) -> Optional[Dict]:
    """Clean and enrich normalized listing data"""
    
    try:
        price_str = normalized_listing.get("price", "0")
        if "–" in str(price_str) or "-" in str(price_str):
            price_str = str(price_str).split("–")[0].split("-")[0]
        digits = re.sub(r'[^\d]', '', str(price_str))
        price = int(digits) if digits else 0
        
        bedrooms_str = normalized_listing.get("bedrooms", "1")
        bedrooms_str_lower = str(bedrooms_str).lower()
        
        if "–" in bedrooms_str or "-" in bedrooms_str:
            matches = re.findall(r'(\d+)', bedrooms_str)
            if matches:
                bedrooms = int(matches[0])
            elif "studio" in bedrooms_str_lower:
                bedrooms = 0
            else:
                bedrooms = 1
        elif "studio" in bedrooms_str_lower:
            bedrooms = 0
        else:
            match = re.search(r'(\d+)', bedrooms_str)
            bedrooms = int(match.group(1)) if match else 1
        
        address = normalized_listing.get("address", "Unknown Address")
        neighborhood = extract_neighborhood(address)
        description = normalized_listing.get("description", "")
        amenities = extract_amenities(description)
        lat, lng = geocode_address(address)
        sqft = 500 + (bedrooms * 200)
        
        apt_id = f"apt_{hash(address) % 100000:05d}"
        
        cleaned = {
            "id": apt_id,
            "address": address,
            "neighborhood": neighborhood,
            "price": price,
            "bedrooms": bedrooms,
            "sqft": sqft,
            "amenities": amenities,
            "lat": lat,
            "lng": lng,
            "link": normalized_listing.get("link", ""),
            "description": description,
            "title": normalized_listing.get("title", "Apartment")
        }
        
        return cleaned
        
    except Exception as e:
        print(f"    Error cleaning listing: {e}")
        return None


def extract_neighborhood(address: str) -> str:
    """Extract neighborhood from address"""
    ottawa_neighborhoods = [
        "Centretown", "Downtown", "Byward", "Glebe", "Hintonburg",
        "Westboro", "Sandy Hill", "Vanier", "Kanata", "Orleans",
        "Barrhaven", "Alta Vista", "Nepean", "Gloucester"
    ]
    
    address_upper = address.upper()
    for neighborhood in ottawa_neighborhoods:
        if neighborhood.upper() in address_upper:
            return neighborhood
    
    return "Downtown"


def extract_amenities(description: str) -> List[str]:
    """Extract amenities from description text"""
    amenities = []
    description_lower = description.lower()
    
    amenity_keywords = {
        "parking": ["parking", "garage", "parking space"],
        "laundry": ["laundry", "washer", "dryer"],
        "gym": ["gym", "fitness", "exercise"],
        "pool": ["pool", "swimming"],
        "pets": ["pet friendly", "pets allowed", "dogs allowed", "cats allowed"],
        "balcony": ["balcony", "terrace", "patio"],
        "dishwasher": ["dishwasher"],
        "ac": ["air conditioning", "a/c", " ac "],
        "heat": ["heat included", "heating"],
        "hydro": ["hydro included", "utilities included"]
    }
    
    for amenity, keywords in amenity_keywords.items():
        if any(keyword in description_lower for keyword in keywords):
            amenities.append(amenity)
    
    return amenities


def geocode_address(address: str) -> tuple:
    """Convert address to lat/lng coordinates"""
    ottawa_coords = {
        "centretown": (45.4215, -75.6972),
        "downtown": (45.4215, -75.6972),
        "byward": (45.4274, -75.6920),
        "glebe": (45.4017, -75.6903),
        "hintonburg": (45.3989, -75.7286),
        "westboro": (45.3896, -75.7594),
        "sandy hill": (45.4225, -75.6796),
        "vanier": (45.4380, -75.6615),
        "kanata": (45.3017, -75.9013),
        "orleans": (45.4766, -75.5100),
        "barrhaven": (45.2732, -75.7370),
        "alta vista": (45.3825, -75.6730),
        "nepean": (45.3250, -75.7250),
        "gloucester": (45.4200, -75.6400)
    }
    
    address_lower = address.lower()
    for neighborhood, coords in ottawa_coords.items():
        if neighborhood in address_lower:
            return coords
    
    return (45.4215, -75.6972)


def get_listings(city: str, budget_min: int, budget_max: int, bedrooms: int, max_results: int = 20) -> List[Dict]:
    """
    Get apartment listings from all enabled sources with caching.
    
    Args:
        city: City name
        budget_min: Minimum monthly rent
        budget_max: Maximum monthly rent
        bedrooms: Number of bedrooms required
        max_results: Maximum number of results to fetch per source
    
    Returns:
        List of cleaned apartment dictionaries matching criteria
    """
    print(f"Fetching listings: {city}, ${budget_min}-${budget_max}, {bedrooms} bed(s), max {max_results} per source")
    
    all_cleaned_listings = []
    sources = get_enabled_sources()
    
    for source_config in sources:
        source_name = source_config['name']
        
        cached = _load_from_cache(source_name, city, budget_min, budget_max, bedrooms)
        if cached:
            all_cleaned_listings.extend(cached)
            continue
        
        raw_listings = fetch_from_source(source_config, city, max_results=max_results)
        
        if not raw_listings:
            continue
        
        source_cleaned_listings = []
        for raw in raw_listings:
            normalized = normalize_listing(raw, source_config)
            if not normalized:
                print(f"    [{source_name}] Failed to normalize a listing")
                continue
            
            cleaned = clean_listing(normalized)
            if cleaned and cleaned["price"] > 0:
                if budget_min <= cleaned["price"] <= budget_max:
                    bed_diff = abs(cleaned["bedrooms"] - bedrooms)
                    if bed_diff <= 1:
                        source_cleaned_listings.append(cleaned)
                    else:
                        print(f"    [{source_name}] Filtered out: {cleaned['title']} - wrong bedrooms ({cleaned['bedrooms']} vs {bedrooms})")
                else:
                    print(f"    [{source_name}] Filtered out: {cleaned['title']} - price ${cleaned['price']} outside ${budget_min}-${budget_max}")
            elif cleaned:
                print(f"    [{source_name}] Filtered out: {cleaned['title']} - no price")
        
        print(f"    [{source_name}] Matched {len(source_cleaned_listings)}/{len(raw_listings)} listings")
        
        if source_cleaned_listings:
            _save_to_cache(source_name, city, budget_min, budget_max, bedrooms, source_cleaned_listings)
            all_cleaned_listings.extend(source_cleaned_listings)
    
    print(f"Total: {len(all_cleaned_listings)} apartments from {len(sources)} sources")
    
    if not all_cleaned_listings:
        print("No listings found. Using mock data.")
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from data.mock_apartments import get_mock_apartments
        return get_mock_apartments(city, budget_min, budget_max, bedrooms)
    
    return all_cleaned_listings
