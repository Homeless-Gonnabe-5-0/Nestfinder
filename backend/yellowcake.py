"""
Yellowcake Service - Live rental data fetching for NestFinder.
Called by ListingAgent to get real-time Ottawa rental listings.
"""

import os
import json
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RentalListing:
    """Normalized rental listing structure."""
    id: str
    address: str
    neighborhood: Optional[str]
    price: int
    bedrooms: Optional[float]
    bathrooms: Optional[float]
    sqft: Optional[int]
    title: str
    description: Optional[str]
    amenities: List[str]
    image_url: Optional[str]
    source_url: str
    pet_friendly: Optional[bool]
    parking_included: Optional[bool]
    laundry_type: Optional[str]
    available_date: Optional[str]
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class YellowcakeService:
    """
    Live rental data service using Yellowcake API.
    """
    
    API_URL = "https://api.yellowcake.dev/v1/extract-stream"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YELLOWCAKE_API_KEY")
        if not self.api_key:
            raise ValueError("Set YELLOWCAKE_API_KEY environment variable")
    
    async def fetch_listings(
        self,
        budget_min: Optional[int] = None,
        budget_max: Optional[int] = None,
        bedrooms: Optional[int] = None,
        limit: int = 30
    ) -> List[RentalListing]:
        """
        Fetch live rental listings from Zumper.
        """
        
        # Build Zumper URL with user's filters
        url = "https://www.zumper.com/apartments-for-rent/ottawa-on"
        
        params = []
        if budget_min:
            params.append(f"price-min={budget_min}")
        if budget_max:
            params.append(f"price-max={budget_max}")
        if bedrooms is not None:
            params.append(f"beds={bedrooms}")
        
        if params:
            url += "?" + "&".join(params)
        
        prompt = f"""
        Extract {limit} rental apartment listings from this Ottawa rentals page.
        
        For each listing, extract:
        - address: Full street address
        - neighborhood: Area/neighborhood name in Ottawa
        - price: Monthly rent in CAD (number only, no $ sign)
        - bedrooms: Number of bedrooms (use 0 for studio/bachelor)
        - bathrooms: Number of bathrooms
        - sqft: Square footage if available
        - title: Listing title
        - description: Brief description if visible
        - amenities: List of amenities (parking, laundry, gym, pool, etc)
        - image_url: Main listing image URL
        - listing_url: Direct URL to the listing detail page
        - pet_friendly: true/false if pets are allowed
        - parking: true/false if parking included
        - laundry: "in_unit", "in_building", or "none"
        - available_date: Move-in date if shown
        - latitude: Latitude coordinate if available
        - longitude: Longitude coordinate if available
        
        Return as JSON array. Only Ottawa listings.
        """
        
        logger.info(f"Fetching live listings: {url}")
        
        raw_data = await self._make_request(url, prompt)
        listings = self._normalize(raw_data)
        
        logger.info(f"Fetched {len(listings)} live listings")
        
        return listings
    
    async def _make_request(self, url: str, prompt: str) -> List[Dict]:
        """Make request to Yellowcake API."""
        
        payload = {"url": url, "prompt": prompt}
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        
        results = []
        timeout = aiohttp.ClientTimeout(total=300)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.API_URL, json=payload, headers=headers) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Yellowcake API error {response.status}: {error_text}")
                
                buffer = ""
                async for chunk in response.content.iter_any():
                    buffer += chunk.decode('utf-8')
                    
                    while "\n\n" in buffer:
                        event, buffer = buffer.split("\n\n", 1)
                        
                        for line in event.split("\n"):
                            if line.startswith("data:"):
                                data_str = line[5:].strip()
                                try:
                                    data = json.loads(data_str)
                                    if data.get("success") and "data" in data:
                                        results = data["data"]
                                        duration = data.get('metadata', {}).get('duration', 0) / 1000
                                        logger.info(f"Yellowcake completed in {duration:.1f}s")
                                except json.JSONDecodeError:
                                    pass
        
        return results
    
    def _normalize(self, raw_listings: List[Dict]) -> List[RentalListing]:
        """Convert raw API data to RentalListing objects."""
        
        listings = []
        
        for i, item in enumerate(raw_listings):
            try:
                price = item.get("price", 0)
                if isinstance(price, str):
                    price = int(''.join(filter(str.isdigit, price)) or 0)
                
                bedrooms = item.get("bedrooms")
                if isinstance(bedrooms, str):
                    if "studio" in bedrooms.lower() or "bachelor" in bedrooms.lower():
                        bedrooms = 0
                    else:
                        bedrooms = float(''.join(filter(lambda x: x.isdigit() or x == '.', bedrooms)) or 0)
                
                laundry = item.get("laundry", "")
                if laundry:
                    laundry = laundry.lower()
                    if "in_unit" in laundry or "in-unit" in laundry:
                        laundry_type = "in_unit"
                    elif "building" in laundry:
                        laundry_type = "in_building"
                    else:
                        laundry_type = "none"
                else:
                    laundry_type = "none"
                
                listing = RentalListing(
                    id=f"zumper_{i}_{hash(item.get('address', '')) % 10000}",
                    address=item.get("address", ""),
                    neighborhood=item.get("neighborhood"),
                    price=price,
                    bedrooms=bedrooms,
                    bathrooms=item.get("bathrooms"),
                    sqft=item.get("sqft"),
                    title=item.get("title", "Rental Listing"),
                    description=item.get("description"),
                    amenities=item.get("amenities", []),
                    image_url=item.get("image_url"),
                    source_url=item.get("listing_url", ""),
                    pet_friendly=item.get("pet_friendly"),
                    parking_included=item.get("parking"),
                    laundry_type=laundry_type,
                    available_date=item.get("available_date"),
                    lat=item.get("latitude"),
                    lng=item.get("longitude"),
                )
                listings.append(listing)
                
            except Exception as e:
                logger.warning(f"Failed to normalize listing: {e}")
        
        return listings


class ListingAgent:
    """
    Listing Agent that uses YellowcakeService for live data.
    """
    
    def __init__(self):
        self.name = "ListingAgent"
        try:
            self.service = YellowcakeService()
            self.live_mode = True
            print(f"[{self.name}] initialized with LIVE Yellowcake data")
        except ValueError as e:
            self.service = None
            self.live_mode = False
            print(f"[{self.name}] WARNING: {e}")
            print(f"[{self.name}] Running in MOCK mode")
    
    async def find_listings(
        self,
        budget_min: int = 0,
        budget_max: int = 5000,
        bedrooms: Optional[int] = None,
        limit: int = 30
    ) -> List[Any]:
        """
        Find apartments matching criteria - LIVE DATA.
        """
        
        print(f"[{self.name}] Fetching {'LIVE' if self.live_mode else 'MOCK'} listings...")
        print(f"   Budget: ${budget_min} - ${budget_max}")
        print(f"   Bedrooms: {bedrooms if bedrooms is not None else 'Any'}")
        
        if not self.live_mode or not self.service:
            return self._get_fallback_listings(budget_min, budget_max, bedrooms, limit)
        
        try:
            listings = await self.service.fetch_listings(
                budget_min=budget_min,
                budget_max=budget_max,
                bedrooms=bedrooms,
                limit=limit
            )
            
            apartments = []
            for listing in listings:
                from models import Apartment
                
                apt = Apartment(
                    id=listing.id,
                    title=listing.title,
                    address=listing.address,
                    neighborhood=listing.neighborhood,
                    price=listing.price,
                    bedrooms=listing.bedrooms,
                    bathrooms=listing.bathrooms,
                    sqft=listing.sqft,
                    description=listing.description,
                    amenities=listing.amenities or [],
                    image_url=listing.image_url,
                    source_url=listing.source_url,
                    pet_friendly=listing.pet_friendly or False,
                    parking_included=listing.parking_included or False,
                    laundry_type=listing.laundry_type or "none",
                    lat=listing.lat,
                    lng=listing.lng,
                )
                apartments.append(apt)
            
            print(f"[{self.name}] Found {len(apartments)} apartments")
            return apartments
            
        except Exception as e:
            print(f"[{self.name}] Error fetching listings: {e}")
            print(f"[{self.name}] Falling back to mock data...")
            return self._get_fallback_listings(budget_min, budget_max, bedrooms, limit)
    
    def _get_fallback_listings(
        self,
        budget_min: int,
        budget_max: int,
        bedrooms: Optional[int],
        limit: int
    ) -> List[Any]:
        """Fallback to mock data if Yellowcake fails."""
        
        from models import Apartment
        
        mock_listings = [
            Apartment(id="mock_001", title="Modern 1BR in Centretown", address="123 Bank Street",
                      neighborhood="Centretown", price=1650, bedrooms=1, bathrooms=1, lat=45.4154, lng=-75.6985),
            Apartment(id="mock_002", title="Spacious 2BR in Glebe", address="456 Bank Street",
                      neighborhood="Glebe", price=2100, bedrooms=2, bathrooms=1, lat=45.3990, lng=-75.6885),
            Apartment(id="mock_003", title="Cozy Studio in ByWard", address="789 Rideau Street",
                      neighborhood="ByWard Market", price=1400, bedrooms=0, bathrooms=1, lat=45.4285, lng=-75.6920),
            Apartment(id="mock_004", title="Bright 1BR in Sandy Hill", address="321 Laurier Ave",
                      neighborhood="Sandy Hill", price=1500, bedrooms=1, bathrooms=1, lat=45.4230, lng=-75.6750),
            Apartment(id="mock_005", title="Large 2BR in Westboro", address="555 Richmond Rd",
                      neighborhood="Westboro", price=2200, bedrooms=2, bathrooms=2, lat=45.3925, lng=-75.7530),
            Apartment(id="mock_006", title="Downtown Studio", address="100 Queen Street",
                      neighborhood="Centretown", price=1350, bedrooms=0, bathrooms=1, lat=45.4200, lng=-75.7000),
            Apartment(id="mock_007", title="3BR Family Home", address="88 Holland Ave",
                      neighborhood="Westboro", price=2800, bedrooms=3, bathrooms=2, lat=45.3950, lng=-75.7400),
            Apartment(id="mock_008", title="1BR Near uOttawa", address="200 King Edward",
                      neighborhood="Sandy Hill", price=1600, bedrooms=1, bathrooms=1, lat=45.4220, lng=-75.6800),
        ]
        
        filtered = [
            apt for apt in mock_listings
            if budget_min <= apt.price <= budget_max
            and (bedrooms is None or apt.bedrooms == bedrooms)
        ]
        
        print(f"[{self.name}] Returning {len(filtered)} mock listings")
        return filtered[:limit]


# Test
async def test():
    print("\n" + "="*60)
    print("Testing ListingAgent")
    print("="*60 + "\n")
    
    agent = ListingAgent()
    
    apartments = await agent.find_listings(
        budget_min=1500,
        budget_max=2500,
        bedrooms=None,
        limit=20
    )
    
    print(f"\nFetched {len(apartments)} apartments:\n")
    
    for apt in apartments[:5]:
        print(f"  {apt.title}")
        print(f"    ${apt.price}/mo | {apt.bedrooms} BR | {apt.neighborhood}")
        print()


if __name__ == "__main__":
    asyncio.run(test())