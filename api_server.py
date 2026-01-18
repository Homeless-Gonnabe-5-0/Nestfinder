"""
Minimal NestFinder API Server
This replaces the heavy backend - just serves the frontend directly from JSON data.
Run with: uvicorn api_server:app --host 0.0.0.0 --port 8080
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="NestFinder API", version="2.0.0")

# CORS - allow frontend from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATA LOADING
# ============================================

LISTINGS_CACHE: Optional[List[Dict]] = None

def get_listings() -> List[Dict]:
    """Load listings from JSON file with caching."""
    global LISTINGS_CACHE
    
    if LISTINGS_CACHE is not None:
        return LISTINGS_CACHE
    
    # Try multiple paths
    paths = [
        Path(__file__).parent / "backend" / "ottawa_rentals.json",
        Path(__file__).parent / "data" / "ottawa_rentals.json",
        Path(__file__).parent / "ottawa_rentals.json",
        Path("backend/ottawa_rentals.json"),
        Path("ottawa_rentals.json"),
    ]
    
    for path in paths:
        if path.exists():
            log.info(f"Loading listings from: {path}")
            with open(path, 'r') as f:
                data = json.load(f)
                LISTINGS_CACHE = data.get("listings", [])
                log.info(f"Loaded {len(LISTINGS_CACHE)} listings")
                return LISTINGS_CACHE
    
    log.warning("No listings file found!")
    LISTINGS_CACHE = []
    return LISTINGS_CACHE


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "user"
    pinned_lat: Optional[float] = None
    pinned_lng: Optional[float] = None
    pet_friendly: Optional[bool] = None
    bedrooms_min: Optional[int] = None
    bathrooms_min: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None


class SearchRequest(BaseModel):
    budget_min: int = 0
    budget_max: int = 5000
    bedrooms: Optional[int] = None
    work_address: Optional[str] = None
    priorities: List[str] = ["low_price"]
    transport_mode: str = "transit"
    max_commute_minutes: int = 45
    pinned_lat: Optional[float] = None
    pinned_lng: Optional[float] = None


# ============================================
# HELPER FUNCTIONS
# ============================================

def filter_listings(
    listings: List[Dict],
    budget_min: int = 0,
    budget_max: int = 10000,
    bedrooms: Optional[int] = None,
    pet_friendly: Optional[bool] = None,
    limit: int = 20
) -> List[Dict]:
    """Filter listings based on criteria."""
    filtered = []
    
    for listing in listings:
        price = listing.get("price", 0)
        beds = listing.get("bedrooms", 0)
        
        if price < budget_min or price > budget_max:
            continue
        
        if bedrooms is not None and beds != bedrooms:
            continue
        
        if pet_friendly and not listing.get("pet_friendly"):
            continue
        
        filtered.append(listing)
        
        if len(filtered) >= limit:
            break
    
    # Sort by price
    filtered.sort(key=lambda x: x.get("price", 0))
    return filtered


def format_recommendation(listing: Dict, rank: int) -> Dict:
    """Format a listing as a recommendation."""
    return {
        "rank": rank,
        "apartment": {
            "id": listing.get("id", ""),
            "title": listing.get("title", "Rental"),
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
        "commute": {
            "apartment_id": listing.get("id", ""),
            "best_mode": "transit",
            "best_time": 20,
            "commute_score": 75,
            "summary": "Good transit access"
        },
        "neighborhood": {
            "apartment_id": listing.get("id", ""),
            "neighborhood_name": listing.get("neighborhood", ""),
            "safety_score": 80,
            "walkability_score": 75,
            "neighborhood_score": 78,
            "summary": f"Located in {listing.get('neighborhood', 'Ottawa')}"
        },
        "budget": {
            "apartment_id": listing.get("id", ""),
            "monthly_rent": listing.get("price", 0),
            "budget_score": 80,
            "is_good_deal": listing.get("price", 0) < 1800,
            "summary": f"${listing.get('price', 0)}/month"
        },
        "overall_score": 85 - rank,
        "headline": f"#{rank} Match - {listing.get('neighborhood', 'Ottawa')}",
        "match_reasons": [
            f"Located in {listing.get('neighborhood', 'Ottawa')}",
            f"${listing.get('price', 0)}/month"
        ],
        "concerns": []
    }


def parse_message(message: str) -> Dict:
    """Parse natural language message to extract search params."""
    message_lower = message.lower()
    params = {
        "budget_min": 0,
        "budget_max": 5000,
        "bedrooms": None,
        "pet_friendly": None,
    }
    
    # Extract price
    price_match = re.search(r'\$?(\d{3,4})', message)
    if price_match:
        price = int(price_match.group(1))
        if any(word in message_lower for word in ["under", "below", "less", "max"]):
            params["budget_max"] = price
        elif any(word in message_lower for word in ["over", "above", "more", "min"]):
            params["budget_min"] = price
        else:
            params["budget_max"] = price
    
    # Extract bedrooms
    bed_match = re.search(r'(\d)\s*(?:bed|br|bedroom)', message_lower)
    if bed_match:
        params["bedrooms"] = int(bed_match.group(1))
    elif "studio" in message_lower or "bachelor" in message_lower:
        params["bedrooms"] = 0
    
    # Pet friendly
    if any(word in message_lower for word in ["pet", "dog", "cat"]):
        params["pet_friendly"] = True
    
    return params


# ============================================
# API ENDPOINTS
# ============================================

@app.get("/api/v1/health")
async def health():
    """Health check endpoint."""
    listings = get_listings()
    return {
        "status": "healthy",
        "version": "2.0.0",
        "listings_count": len(listings)
    }


@app.get("/api/v1/priorities")
async def get_priorities():
    """Get available search priorities."""
    return {
        "priorities": [
            "short_commute",
            "low_price",
            "safe_area",
            "walkable",
            "parking",
            "pet_friendly"
        ]
    }


@app.get("/api/v1/neighborhoods")
async def get_neighborhoods():
    """Get list of neighborhoods."""
    listings = get_listings()
    neighborhoods = set()
    for listing in listings:
        n = listing.get("neighborhood")
        if n:
            neighborhoods.add(n)
    return {"neighborhoods": sorted(list(neighborhoods))}


@app.get("/api/v1/transport-modes")
async def get_transport_modes():
    """Get available transport modes."""
    return {"modes": ["transit", "driving", "biking", "walking"]}


@app.post("/api/v1/search")
async def search_apartments(request: SearchRequest):
    """Search for apartments."""
    listings = get_listings()
    
    filtered = filter_listings(
        listings,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        bedrooms=request.bedrooms,
        limit=20
    )
    
    recommendations = [
        format_recommendation(listing, i + 1)
        for i, listing in enumerate(filtered)
    ]
    
    return {
        "search_id": "search_001",
        "total_found": len(filtered),
        "recommendations": recommendations,
        "search_params": request.dict(),
        "searched_at": "2026-01-18T00:00:00Z"
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    Natural language chat endpoint.
    This is what the frontend calls.
    """
    listings = get_listings()
    
    # Parse the message to extract search parameters
    params = parse_message(request.message)
    
    # Apply any explicit filters from the request
    if request.price_max:
        params["budget_max"] = request.price_max
    if request.price_min:
        params["budget_min"] = request.price_min
    if request.bedrooms_min is not None:
        params["bedrooms"] = request.bedrooms_min
    if request.pet_friendly:
        params["pet_friendly"] = request.pet_friendly
    
    # Filter listings
    filtered = filter_listings(
        listings,
        budget_min=params["budget_min"],
        budget_max=params["budget_max"],
        bedrooms=params["bedrooms"],
        pet_friendly=params["pet_friendly"],
        limit=10
    )
    
    # Build response text
    if filtered:
        response_text = f"I found {len(filtered)} apartments"
        
        if params["budget_max"] < 5000:
            response_text += f" under ${params['budget_max']}/month"
        if params["bedrooms"] is not None:
            beds = params["bedrooms"]
            response_text += f" with {beds} bedroom{'s' if beds != 1 else ''}" if beds > 0 else " (studios)"
        
        response_text += ".\n\nHere are your top matches:\n\n"
        
        for i, listing in enumerate(filtered[:5], 1):
            response_text += f"**{listing.get('title', 'Rental')}**\n"
            response_text += f"${listing.get('price', 0)}/mo • "
            response_text += f"{listing.get('bedrooms', 0)} BR • "
            response_text += f"{listing.get('neighborhood', 'Ottawa')}\n"
            if listing.get("source_url"):
                response_text += f"{listing['source_url']}\n"
            response_text += "\n"
    else:
        response_text = "I couldn't find apartments matching those criteria. Try adjusting your budget or bedroom requirements."
    
    # Build search results
    recommendations = [
        format_recommendation(listing, i + 1)
        for i, listing in enumerate(filtered)
    ]
    
    search_results = {
        "search_id": "chat_search",
        "total_found": len(filtered),
        "recommendations": recommendations,
        "search_params": params,
        "searched_at": "2026-01-18T00:00:00Z"
    } if filtered else None
    
    return {
        "response": response_text,
        "intent": "search" if filtered else "chat",
        "search_results": search_results
    }


# ============================================
# STARTUP
# ============================================

@app.on_event("startup")
async def startup():
    """Pre-load listings on startup."""
    listings = get_listings()
    log.info(f"API Server ready with {len(listings)} listings")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)