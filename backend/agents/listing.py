# agents/listing.py - Listing Agent that loads from JSON files

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment

# Paths to JSON files
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "scraped")
KIJIJI_FILE = os.path.join(DATA_DIR, "kijiji.json")
ZUMPER_FILE = os.path.join(DATA_DIR, "zumper.json")
HOMESTEAD_FILE = os.path.join(DATA_DIR, "homestead.json")


class ListingAgent:
    """
    Finds apartments from our scraped JSON files.
    Loads from kijiji.json and zumper.json
    """
    
    def __init__(self):
        self.name = "ListingAgent"
        self.apartments = []
        self._load_all_apartments()
        print(f"[{self.name}] initialized with {len(self.apartments)} apartments")
    
    def _load_all_apartments(self):
        """Load all apartments from JSON files"""
        self.apartments = []
        
        # Load Kijiji
        if os.path.exists(KIJIJI_FILE):
            try:
                with open(KIJIJI_FILE, 'r') as f:
                    data = json.load(f)
                kijiji_listings = data if isinstance(data, list) else []
                for i, listing in enumerate(kijiji_listings):
                    apt = self._parse_kijiji(listing, i)
                    if apt:
                        self.apartments.append(apt)
                print(f"[{self.name}] Loaded {len(kijiji_listings)} from Kijiji")
            except Exception as e:
                print(f"[{self.name}] Error loading Kijiji: {e}")
        
        # Load Zumper
        if os.path.exists(ZUMPER_FILE):
            try:
                with open(ZUMPER_FILE, 'r') as f:
                    data = json.load(f)
                zumper_listings = data.get("listings", [])
                for i, listing in enumerate(zumper_listings):
                    apt = self._parse_zumper(listing, i)
                    if apt:
                        self.apartments.append(apt)
                print(f"[{self.name}] Loaded {len(zumper_listings)} from Zumper")
            except Exception as e:
                print(f"[{self.name}] Error loading Zumper: {e}")
        
        # Load Homestead
        if os.path.exists(HOMESTEAD_FILE):
            try:
                with open(HOMESTEAD_FILE, 'r') as f:
                    data = json.load(f)
                homestead_listings = data.get("listings", [])
                for i, listing in enumerate(homestead_listings):
                    apt = self._parse_homestead(listing, i)
                    if apt:
                        self.apartments.append(apt)
                print(f"[{self.name}] Loaded {len(homestead_listings)} from Homestead")
            except Exception as e:
                print(f"[{self.name}] Error loading Homestead: {e}")
        
        print(f"[{self.name}] Total: {len(self.apartments)} apartments")
    
    def _parse_price(self, price_str) -> int:
        """Parse price from string like '$1,913' or 2030"""
        if isinstance(price_str, int):
            return price_str
        if isinstance(price_str, float):
            return int(price_str)
        if not price_str:
            return 0
        # Remove $ and commas, get digits
        digits = re.sub(r'[^\d]', '', str(price_str))
        return int(digits) if digits else 0
    
    def _parse_kijiji(self, listing: dict, index: int) -> Apartment:
        """Parse a Kijiji listing into an Apartment"""
        try:
            price = self._parse_price(listing.get("monthly_rent", 0))
            if price == 0:
                return None
            
            # Extract amenities
            raw_amenities = listing.get("amenities", [])
            amenities = [a.lower() for a in raw_amenities] if raw_amenities else []
            
            # Check for features
            pet_friendly = any("pet" in a.lower() for a in raw_amenities)
            parking = any("parking" in a.lower() for a in raw_amenities)
            has_laundry = any("laundry" in a.lower() for a in raw_amenities)
            
            # Get coordinates from neighborhood
            lat, lng = self._get_coords(listing.get("neighborhood_name", ""))
            
            return Apartment(
                id=f"kijiji_{index}",
                title=listing.get("listing_title", "Apartment"),
                address=listing.get("full_address", "Ottawa, ON"),
                neighborhood=listing.get("neighborhood_name", "Ottawa"),
                price=price,
                bedrooms=listing.get("bedrooms", 1) or 1,
                bathrooms=1.0,
                sqft=listing.get("square_footage") or 500,
                amenities=amenities,
                pet_friendly=pet_friendly,
                parking_included=parking,
                laundry_type="in_unit" if has_laundry else "none",
                image_url=listing.get("main_image_url"),
                source_url=listing.get("listing_link"),
                lat=lat,
                lng=lng
            )
        except Exception as e:
            print(f"[ListingAgent] Error parsing Kijiji listing: {e}")
            return None
    
    def _parse_homestead(self, listing: dict, index: int) -> Apartment:
        """Parse a Homestead listing into an Apartment"""
        try:
            price = listing.get("price")
            if not price or price == 0:
                return None
            
            bedrooms = listing.get("bedrooms", 1)
            if bedrooms == "Studio":
                bedrooms = 0
            
            # Get coordinates from address
            lat, lng = self._get_coords(listing.get("neighborhood", "") or listing.get("address", ""))
            
            return Apartment(
                id=listing.get("id", f"homestead_{index}"),
                title=listing.get("title", "Apartment"),
                address=listing.get("address", "Ottawa, ON"),
                neighborhood=listing.get("neighborhood", "Ottawa"),
                price=price,
                bedrooms=bedrooms if isinstance(bedrooms, int) else 1,
                bathrooms=listing.get("bathrooms", 1.0),
                sqft=500 + (bedrooms * 200) if isinstance(bedrooms, int) else 500,
                amenities=[],
                pet_friendly=False,
                parking_included=False,
                laundry_type="none",
                image_url=listing.get("image_url"),
                source_url=listing.get("url"),
                lat=lat,
                lng=lng
            )
        except Exception as e:
            print(f"[ListingAgent] Error parsing Homestead listing: {e}")
            return None
    
    def _parse_zumper(self, listing: dict, index: int) -> Apartment:
        """Parse a Zumper listing into an Apartment"""
        try:
            price = self._parse_price(listing.get("monthly_rent", 0))
            if price == 0:
                return None
            
            # Extract amenities
            raw_amenities = listing.get("amenities", [])
            amenities = [a.lower() for a in raw_amenities] if raw_amenities else []
            
            # Check for features
            pet_friendly = any("pet" in a.lower() for a in raw_amenities)
            parking = any("parking" in a.lower() for a in raw_amenities)
            has_laundry = any("laundry" in a.lower() for a in raw_amenities)
            
            # Get coordinates from neighborhood
            lat, lng = self._get_coords(listing.get("neighborhood", ""))
            
            return Apartment(
                id=f"zumper_{index}",
                title=listing.get("listing_title", "Apartment"),
                address=listing.get("full_address", "Ottawa, ON"),
                neighborhood=listing.get("neighborhood", "Ottawa"),
                price=price,
                bedrooms=listing.get("bedrooms", 1) or 1,
                bathrooms=1.0,
                sqft=listing.get("sqft") or 500,
                amenities=amenities,
                pet_friendly=pet_friendly,
                parking_included=parking,
                laundry_type="in_unit" if has_laundry else "none",
                image_url=listing.get("image_url"),
                source_url=listing.get("listing_url"),
                lat=lat,
                lng=lng
            )
        except Exception as e:
            print(f"[ListingAgent] Error parsing Zumper listing: {e}")
            return None
    
    def _get_coords(self, neighborhood: str) -> tuple:
        """Get approximate coordinates for a neighborhood"""
        coords = {
            "centretown": (45.4153, -75.6979),
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
            "gloucester": (45.4200, -75.6400),
            "little italy": (45.4066, -75.7125),
            "somerset": (45.4153, -75.6979),
            "ottawa": (45.4215, -75.6972),
        }
        
        neighborhood_lower = neighborhood.lower()
        for name, coord in coords.items():
            if name in neighborhood_lower:
                return coord
        
        # Default to downtown Ottawa
        return (45.4215, -75.6972)
    
    async def find_listings(
        self,
        budget_min: int,
        budget_max: int,
        bedrooms: int = 1,
        limit: int = 20,
        **kwargs
    ) -> list:
        """
        Find apartments matching criteria from our JSON data.
        
        Returns: List of Apartment objects
        """
        print(f"[{self.name}] Searching ${budget_min}-${budget_max}, {bedrooms}BR")
        
        matching = []
        for apt in self.apartments:
            # Filter by price
            if apt.price < budget_min or apt.price > budget_max:
                continue
            
            # Filter by bedrooms (allow +/- 1)
            if abs(apt.bedrooms - bedrooms) > 1:
                continue
            
            matching.append(apt)
        
        # Sort by price
        matching.sort(key=lambda x: x.price)
        
        results = matching[:limit]
        print(f"[{self.name}] Found {len(results)} apartments (from {len(matching)} matches)")
        return results


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = ListingAgent()
        
        print("\n--- Test 1: $1500-$2000, 1BR ---")
        apartments = await agent.find_listings(1500, 2000, 1)
        for apt in apartments[:5]:
            print(f"  ${apt.price} - {apt.title[:40]} ({apt.neighborhood})")
        
        print("\n--- Test 2: $2000-$3000, 2BR ---")
        apartments = await agent.find_listings(2000, 3000, 2)
        for apt in apartments[:5]:
            print(f"  ${apt.price} - {apt.title[:40]} ({apt.neighborhood})")
    
    asyncio.run(test())
