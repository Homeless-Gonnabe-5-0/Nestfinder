# agents/listing.py - Listing Agent (Person 2 will improve this later)
# This is a working stub so we can test the full system

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment
from data.mock_apartments import get_mock_apartments


class ListingAgent:
    """
    Finds apartments matching user criteria.
    Uses Yellowcake API to scrape listings (falls back to mock data).
    """
    
    def __init__(self):
        self.name = "ListingAgent"
        print(f"[{self.name}] initialized")
    
    async def find_listings(
        self,
        budget_min: int,
        budget_max: int,
        bedrooms: int = 1,
        limit: int = 20
    ) -> list:
        """
        Find apartments matching criteria.
        
        Returns: List of Apartment objects
        """
        print(f"[{self.name}] Searching ${budget_min}-${budget_max}, {bedrooms}BR")
        
        # TODO: Person 2 will add Yellowcake integration here
        # For now, use mock data
        apartments = get_mock_apartments(budget_min, budget_max, bedrooms)
        apartments = apartments[:limit]
        
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