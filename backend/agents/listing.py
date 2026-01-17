import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment
from services.scraper import get_listings
from constants import CITY


class ListingAgent:
    """
    Finds apartments matching user criteria using Yellowcake API + Zumper.
    Falls back to mock data if API unavailable.
    """
    
    def __init__(self):
        self.name = "ListingAgent"
        print(f"[{self.name}] initialized")
    
    async def find_listings(
        self,
        budget_min: int,
        budget_max: int,
        bedrooms: int = 1,
        limit: int = 20,
        max_results_per_source: int = 20
    ) -> list:
        """
        Find apartments matching criteria via Yellowcake API.
        
        Returns: List of Apartment objects
        """
        print(f"[{self.name}] Searching ${budget_min}-${budget_max}, {bedrooms}BR")
        
        raw_listings = get_listings(CITY, budget_min, budget_max, bedrooms, max_results=max_results_per_source)
        apartments = []
        
        for listing in raw_listings[:limit]:
            apt = Apartment(
                id=listing['id'],
                title=listing.get('title', 'Apartment'),
                address=listing['address'],
                neighborhood=listing['neighborhood'],
                price=listing['price'],
                bedrooms=listing['bedrooms'],
                bathrooms=1.0,
                sqft=listing['sqft'],
                amenities=listing['amenities'],
                lat=listing['lat'],
                lng=listing['lng'],
                source_url=listing.get('link', ''),
                pet_friendly='pets' in listing['amenities'],
                parking_included='parking' in listing['amenities'],
                laundry_type='in-unit' if 'laundry' in listing['amenities'] else 'none'
            )
            apartments.append(apt)
        
        print(f"[{self.name}] Found {len(apartments)} apartments")
        return apartments


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = ListingAgent()
        apartments = await agent.find_listings(1500, 2000, 1)
        for apt in apartments:
            print(f"  - {apt.title}: ${apt.price}")
    
    asyncio.run(test())