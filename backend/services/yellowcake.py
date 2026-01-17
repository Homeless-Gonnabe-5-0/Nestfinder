import os
from dotenv import load_dotenv
import requests
from typing import List, Dict, Optional

# Load environment variables from .env file
load_dotenv()

YELLOWCAKE_API_URL = "https://api.yellowcake.dev/v1/extract-stream"
YELLOWCAKE_API_KEY = os.getenv("YELLOWCAKE_API_KEY")


def fetch_raw_listings(city: str, max_results: int = 20) -> List[Dict]:
    """
    Fetch raw apartment rental listings for a given city using Yellowcake API.
    
    Args:
        city: City name (e.g., "Ottawa")
        max_results: Maximum number of listings to return
    
    Returns:
        List of raw listing dictionaries
        Returns [] if API fails or no data found
    """
    
    if not YELLOWCAKE_API_KEY:
        print("⚠️  Yellowcake API key not found. Check your .env file.")
        print("   Create a .env file in your project root with:")
        print("   YELLOWCAKE_API_KEY=your_api_key_here")
        return []

    headers = {
        "Authorization": f"Bearer {YELLOWCAKE_API_KEY}",
        "Content-Type": "application/json"
    }

    # Yellowcake needs a URL to scrape
    # Let's scrape Kijiji Ottawa apartments
    target_url = f"https://www.kijiji.ca/b-apartments-condos/{city.lower()}/k0c37l1700185"
    
    payload = {
        "url": target_url,
        "extract": {
            "schema": {
                "listings": [
                    {
                        "title": "string",
                        "price": "string",
                        "address": "string",
                        "bedrooms": "string",
                        "description": "string",
                        "link": "string"
                    }
                ]
            }
        }
    }

    try:
        print(f"🔍 Scraping: {target_url}")
        response = requests.post(
            YELLOWCAKE_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract listings from Yellowcake response
        listings = data.get("data", {}).get("listings", [])
        print(f"✅ Yellowcake API: Found {len(listings)} raw listings")
        return listings
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Yellowcake API HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text[:500]}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Yellowcake API Request Error: {e}")
        return []
    except Exception as e:
        print(f"❌ Yellowcake API Unexpected Error: {e}")
        return []


def clean_listing(raw_listing: Dict) -> Optional[Dict]:
    """
    Convert raw Yellowcake listing to standardized apartment format.
    
    Expected output format:
    {
        "id": "apt_001",
        "address": "245 Laurier Ave, Ottawa",
        "neighborhood": "Centretown",
        "price": 1750,
        "bedrooms": 1,
        "sqft": 650,
        "amenities": ["parking", "laundry"],
        "lat": 45.4215,
        "lng": -75.6972
    }
    """
    try:
        import re
        
        # Extract price (handle various formats: "$1,750", "1750", "$1750/month")
        price_str = raw_listing.get("price", "0")
        digits = re.sub(r'[^\d]', '', str(price_str))
        price = int(digits) if digits else 0
        
        # Extract bedrooms
        bedrooms_str = raw_listing.get("bedrooms", "1")
        match = re.search(r'(\d+)', str(bedrooms_str))
        bedrooms = int(match.group(1)) if match else 1
        
        # Extract address
        address = raw_listing.get("address", "Unknown Address, Ottawa")
        
        # Generate unique ID
        apt_id = f"apt_{hash(address) % 100000:05d}"
        
        # Parse neighborhood from address (simple version)
        neighborhood = extract_neighborhood(address)
        
        # Extract amenities from description
        description = raw_listing.get("description", "")
        amenities = extract_amenities(description)
        
        # Geocode address to lat/lng
        lat, lng = geocode_address(address)
        
        # Extract square footage if available (default to estimate based on bedrooms)
        sqft = raw_listing.get("sqft", 500 + (bedrooms * 200))
        
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
            "link": raw_listing.get("link", ""),
            "description": description
        }
        
        return cleaned
        
    except Exception as e:
        print(f"⚠️  Error cleaning listing: {e}")
        return None


def extract_neighborhood(address: str) -> str:
    """Extract neighborhood from address."""
    ottawa_neighborhoods = [
        "Centretown", "Downtown", "Byward", "Glebe", "Hintonburg",
        "Westboro", "Sandy Hill", "Vanier", "Kanata", "Orleans",
        "Barrhaven", "Alta Vista", "Nepean", "Gloucester"
    ]
    
    address_upper = address.upper()
    for neighborhood in ottawa_neighborhoods:
        if neighborhood.upper() in address_upper:
            return neighborhood
    
    return "Downtown"  # Default


def extract_amenities(description: str) -> List[str]:
    """Extract amenities from description text."""
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
    """Convert address to lat/lng coordinates."""
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
    
    # Default to downtown Ottawa
    return (45.4215, -75.6972)


def get_listings(city: str, budget_min: int, budget_max: int, bedrooms: int) -> List[Dict]:
    """
    Main function to get cleaned apartment listings.
    
    Args:
        city: City name (e.g., "Ottawa")
        budget_min: Minimum monthly rent
        budget_max: Maximum monthly rent
        bedrooms: Number of bedrooms required
    
    Returns:
        List of cleaned apartment dictionaries matching criteria
    """
    print(f"🔍 Fetching listings for {city}: ${budget_min}-${budget_max}, {bedrooms} bed(s)")
    
    # Try Yellowcake API first
    raw_listings = fetch_raw_listings(city)
    
    # If API fails, use mock data
    if not raw_listings:
        print("⚠️  Yellowcake API returned no results. Using mock data.")
        from backend.data.mock_apartments import get_mock_apartments
        return get_mock_apartments(city, budget_min, budget_max, bedrooms)
    
    # Clean and filter listings
    cleaned_listings = []
    for raw in raw_listings:
        cleaned = clean_listing(raw)
        if cleaned and cleaned["price"] > 0:  # Skip listings with no price
            # Filter by criteria
            if (budget_min <= cleaned["price"] <= budget_max and 
                cleaned["bedrooms"] == bedrooms):
                cleaned_listings.append(cleaned)
    
    print(f"✅ Found {len(cleaned_listings)} apartments matching criteria")
    
    # If no matches, fall back to mock data
    if not cleaned_listings:
        print("⚠️  No listings matched criteria. Using mock data.")
        from backend.data.mock_apartments import get_mock_apartments
        return get_mock_apartments(city, budget_min, budget_max, bedrooms)
    
    return cleaned_listings


# Testing
if __name__ == "__main__":
    print("Testing Yellowcake integration...")
    listings = get_listings("Ottawa", 1500, 2000, 1)
    
    if listings:
        print(f"\n📋 Sample listing:")
        import json
        print(json.dumps(listings[0], indent=2))
    else:
        print("No listings found")