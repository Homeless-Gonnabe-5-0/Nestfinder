"""NestFinder SAM Tools - Direct data access (no separate backend needed)"""
import json
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

log = logging.getLogger(__name__)

# Find the data file - adjust path as needed
DATA_DIR = Path(__file__).parent.parent / "data"
LISTINGS_FILE = DATA_DIR / "ottawa_rentals.json"

# Fallback paths to try
FALLBACK_PATHS = [
    Path(__file__).parent.parent / "backend" / "ottawa_rentals.json",
    Path(__file__).parent / "ottawa_rentals.json",
    Path("/Users/inesiraoui/Desktop/nestfinder/backend/ottawa_rentals.json"),
]

# Cache for listings
_listings_cache: Optional[List[Dict]] = None


def _load_listings() -> List[Dict]:
    """Load listings from JSON file with caching."""
    global _listings_cache
    
    if _listings_cache is not None:
        return _listings_cache
    
    # Try to find the listings file
    paths_to_try = [LISTINGS_FILE] + FALLBACK_PATHS
    
    for path in paths_to_try:
        if path.exists():
            log.info(f"Loading listings from: {path}")
            with open(path, 'r') as f:
                data = json.load(f)
                _listings_cache = data.get("listings", [])
                log.info(f"Loaded {len(_listings_cache)} listings")
                return _listings_cache
    
    log.warning("No listings file found, using empty list")
    _listings_cache = []
    return _listings_cache


def _filter_listings(
    listings: List[Dict],
    budget_min: int = 0,
    budget_max: int = 10000,
    bedrooms: Optional[int] = None,
    pet_friendly: Optional[bool] = None,
    neighborhood: Optional[str] = None,
    limit: int = 20
) -> List[Dict]:
    """Filter listings based on criteria."""
    filtered = []
    
    for listing in listings:
        price = listing.get("price", 0)
        beds = listing.get("bedrooms", 0)
        
        # Budget filter
        if price < budget_min or price > budget_max:
            continue
        
        # Bedrooms filter
        if bedrooms is not None and beds != bedrooms:
            continue
        
        # Pet friendly filter
        if pet_friendly is not None and pet_friendly:
            if not listing.get("pet_friendly"):
                continue
        
        # Neighborhood filter
        if neighborhood:
            listing_neighborhood = listing.get("neighborhood", "").lower()
            if neighborhood.lower() not in listing_neighborhood:
                continue
        
        filtered.append(listing)
        
        if len(filtered) >= limit:
            break
    
    return filtered


def _format_listing_response(listing: Dict, rank: int = 1) -> Dict:
    """Format a listing for the response."""
    return {
        "rank": rank,
        "apartment": {
            "id": listing.get("id", ""),
            "title": listing.get("title", "Rental Listing"),
            "address": listing.get("address", ""),
            "neighborhood": listing.get("neighborhood", "Ottawa"),
            "price": listing.get("price", 0),
            "bedrooms": listing.get("bedrooms", 0),
            "bathrooms": listing.get("bathrooms", 1),
            "sqft": listing.get("sqft"),
            "amenities": listing.get("amenities", []),
            "pet_friendly": listing.get("pet_friendly", False),
            "parking_included": listing.get("parking") is not None,
            "laundry_type": listing.get("laundry", "none"),
            "image_url": listing.get("image_url"),
            "source_url": listing.get("source_url", ""),
            "lat": listing.get("lat"),
            "lng": listing.get("lng"),
        },
        "overall_score": 85 - (rank * 2),  # Simple scoring
        "headline": f"#{rank} Match",
        "match_reasons": _generate_match_reasons(listing),
        "concerns": [],
    }


def _generate_match_reasons(listing: Dict) -> List[str]:
    """Generate match reasons based on listing features."""
    reasons = []
    
    if listing.get("price", 0) < 1500:
        reasons.append("Great price point")
    
    amenities = listing.get("amenities", [])
    if any("laundry" in a.lower() for a in amenities):
        reasons.append("Has laundry")
    if any("parking" in a.lower() for a in amenities):
        reasons.append("Parking available")
    if any("gym" in a.lower() or "fitness" in a.lower() for a in amenities):
        reasons.append("Fitness center")
    
    neighborhood = listing.get("neighborhood", "")
    if neighborhood:
        reasons.append(f"Located in {neighborhood}")
    
    if not reasons:
        reasons.append("Good location")
    
    return reasons[:3]


# ============================================
# SAM TOOLS - These are called by the agent
# ============================================

async def search_apartments(
    budget_min: int = 0,
    budget_max: int = 3000,
    bedrooms: Optional[int] = None,
    pet_friendly: Optional[bool] = None,
    neighborhood: Optional[str] = None,
    limit: int = 10,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search for apartments in Ottawa based on criteria.
    
    Args:
        budget_min: Minimum monthly rent
        budget_max: Maximum monthly rent  
        bedrooms: Number of bedrooms (0 for studio, None for any)
        pet_friendly: Filter for pet-friendly units
        neighborhood: Filter by neighborhood name
        limit: Maximum results to return
    
    Returns:
        Search results with apartment listings
    """
    try:
        listings = _load_listings()
        
        filtered = _filter_listings(
            listings,
            budget_min=budget_min,
            budget_max=budget_max,
            bedrooms=bedrooms,
            pet_friendly=pet_friendly,
            neighborhood=neighborhood,
            limit=limit
        )
        
        recommendations = [
            _format_listing_response(listing, rank=i+1)
            for i, listing in enumerate(filtered)
        ]
        
        return {
            "status": "success",
            "total_found": len(filtered),
            "recommendations": recommendations,
            "search_params": {
                "budget_min": budget_min,
                "budget_max": budget_max,
                "bedrooms": bedrooms,
                "pet_friendly": pet_friendly,
                "neighborhood": neighborhood,
            }
        }
        
    except Exception as e:
        log.error(f"Search error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "recommendations": []
        }


async def chat_nestfinder(
    message: str,
    session_id: str = "sam_user",
    pinned_lat: Optional[float] = None,
    pinned_lng: Optional[float] = None,
    pet_friendly: Optional[bool] = None,
    bedrooms_min: Optional[int] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process a natural language chat message about apartments.
    
    This tool interprets the user's message and searches for apartments.
    
    Args:
        message: User's natural language query
        session_id: Session identifier
        pinned_lat: Pinned location latitude (for commute calc)
        pinned_lng: Pinned location longitude
        pet_friendly: Filter for pet-friendly
        bedrooms_min: Minimum bedrooms
        price_min: Minimum price
        price_max: Maximum price
    
    Returns:
        Chat response with search results if applicable
    """
    try:
        # Parse intent from message
        message_lower = message.lower()
        
        # Extract budget from message
        budget_max = price_max or 3000
        budget_min = price_min or 0
        
        # Look for price mentions
        import re
        price_match = re.search(r'\$?(\d{3,4})', message)
        if price_match and not price_max:
            mentioned_price = int(price_match.group(1))
            if "under" in message_lower or "below" in message_lower or "less than" in message_lower:
                budget_max = mentioned_price
            elif "over" in message_lower or "above" in message_lower or "more than" in message_lower:
                budget_min = mentioned_price
            else:
                # Assume it's a max budget
                budget_max = mentioned_price
        
        # Extract bedrooms
        bedrooms = bedrooms_min
        if bedrooms is None:
            bed_match = re.search(r'(\d)\s*(?:bed|br|bedroom)', message_lower)
            if bed_match:
                bedrooms = int(bed_match.group(1))
            elif "studio" in message_lower or "bachelor" in message_lower:
                bedrooms = 0
        
        # Extract neighborhood
        neighborhood = None
        neighborhoods = ["centretown", "glebe", "westboro", "sandy hill", "byward", 
                        "hintonburg", "little italy", "old ottawa", "kanata", "orleans",
                        "nepean", "barrhaven", "downtown"]
        for n in neighborhoods:
            if n in message_lower:
                neighborhood = n
                break
        
        # Check for pet mention
        if pet_friendly is None:
            if "pet" in message_lower or "dog" in message_lower or "cat" in message_lower:
                pet_friendly = True
        
        # Search apartments
        search_result = await search_apartments(
            budget_min=budget_min,
            budget_max=budget_max,
            bedrooms=bedrooms,
            pet_friendly=pet_friendly,
            neighborhood=neighborhood,
            limit=10
        )
        
        # Generate response text
        if search_result["status"] == "success" and search_result["recommendations"]:
            count = len(search_result["recommendations"])
            response_text = f"I found {count} apartments matching your criteria"
            
            if budget_max < 3000:
                response_text += f" under ${budget_max}/month"
            if bedrooms is not None:
                response_text += f" with {bedrooms} bedroom{'s' if bedrooms != 1 else ''}"
            if neighborhood:
                response_text += f" in {neighborhood.title()}"
            
            response_text += ".\n\nHere are the top matches:\n\n"
            
            for rec in search_result["recommendations"][:5]:
                apt = rec["apartment"]
                response_text += f"**{apt['title']}**\n"
                response_text += f"${apt['price']}/mo • {apt['bedrooms']} BR • {apt['neighborhood']}\n"
                if apt.get("source_url"):
                    response_text += f"View: {apt['source_url']}\n"
                response_text += "\n"
        else:
            response_text = "I couldn't find apartments matching those criteria. Try adjusting your budget or bedroom requirements."
        
        return {
            "status": "success",
            "response": response_text,
            "intent": "search",
            "search_results": search_result if search_result["status"] == "success" else None
        }
        
    except Exception as e:
        log.error(f"Chat error: {e}")
        return {
            "status": "error",
            "response": f"Sorry, I encountered an error: {str(e)}",
            "intent": "error",
            "search_results": None
        }


async def get_neighborhoods(
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get list of Ottawa neighborhoods with listings."""
    try:
        listings = _load_listings()
        neighborhoods = set()
        
        for listing in listings:
            n = listing.get("neighborhood")
            if n:
                neighborhoods.add(n)
        
        return {
            "status": "success",
            "neighborhoods": sorted(list(neighborhoods))
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "neighborhoods": []
        }


async def get_priorities(
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get available search priorities."""
    return {
        "status": "success",
        "priorities": [
            "short_commute",
            "low_price",
            "safe_area",
            "walkable",
            "parking",
            "pet_friendly",
            "in_unit_laundry",
            "quiet_area"
        ]
    }


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing apartment tools...")
        
        # Test search
        result = await search_apartments(
            budget_max=2000,
            bedrooms=1,
            limit=5
        )
        print(f"\nSearch result: {result['status']}")
        print(f"Found: {result.get('total_found', 0)} apartments")
        
        # Test chat
        chat_result = await chat_nestfinder(
            message="Find me 1 bedroom apartments under $1800 in Centretown"
        )
        print(f"\nChat response:\n{chat_result.get('response', '')[:500]}")
        
        # Test neighborhoods
        neighborhoods = await get_neighborhoods()
        print(f"\nNeighborhoods: {neighborhoods.get('neighborhoods', [])[:10]}")
    
    asyncio.run(test())