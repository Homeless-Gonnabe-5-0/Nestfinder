"""
NestFinder Apartment Tools for SAM agents.
Uses ottawa_rentals.json (190 real Ottawa listings from Zumper).
"""

import json
import os
import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# Load rental data from JSON file
_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ottawa_rentals.json")
_listings_cache = None
_apartments_cache: Dict[str, Dict] = {}


def _load_listings() -> List[Dict]:
    """Load listings from JSON file."""
    global _listings_cache
    if _listings_cache is None:
        try:
            with open(_DATA_PATH, 'r') as f:
                data = json.load(f)
                _listings_cache = data.get("listings", [])
            log.info(f"Loaded {len(_listings_cache)} Ottawa rental listings from JSON")
        except Exception as e:
            log.error(f"Failed to load listings: {e}")
            _listings_cache = []
    return _listings_cache


def _normalize_laundry(laundry: Optional[str]) -> str:
    """Convert laundry string to standard format."""
    if not laundry:
        return "none"
    laundry = laundry.lower()
    if "in-unit" in laundry or "in unit" in laundry:
        return "in_unit"
    elif "on-site" in laundry or "building" in laundry:
        return "in_building"
    return "none"


def _has_parking(listing: Dict) -> bool:
    """Check if listing includes parking."""
    parking = listing.get("parking")
    if parking:
        return True
    amenities = listing.get("amenities", [])
    return any("parking" in str(a).lower() for a in amenities)


def _is_pet_friendly(listing: Dict) -> bool:
    """Check if listing allows pets."""
    pet = listing.get("pet_friendly")
    if pet is True:
        return True
    amenities = listing.get("amenities", [])
    return any("pet" in str(a).lower() for a in amenities)


def _listing_to_apartment(listing: Dict) -> Dict:
    """Convert raw listing to apartment format."""
    return {
        "id": listing.get("id"),
        "title": listing.get("title", "Rental Listing"),
        "address": listing.get("address", ""),
        "neighborhood": listing.get("neighborhood", "Unknown"),
        "price": listing.get("price", 0),
        "bedrooms": listing.get("bedrooms", 0),
        "bathrooms": listing.get("bathrooms", 1),
        "sqft": listing.get("sqft"),
        "amenities": listing.get("amenities", []),
        "pet_friendly": _is_pet_friendly(listing),
        "parking_included": _has_parking(listing),
        "laundry_type": _normalize_laundry(listing.get("laundry")),
        "image_url": listing.get("image_url"),
        "source_url": listing.get("source_url"),
    }


# =============================================================================
# TOOL 1: Search Apartments
# =============================================================================

async def search_apartments(
    budget_min: int = 0,
    budget_max: int = 5000,
    bedrooms: Optional[int] = None,
    neighborhood: Optional[str] = None,
    pet_friendly: Optional[bool] = None,
    parking_required: Optional[bool] = None,
    limit: int = 20,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search for apartments in Ottawa based on criteria.

    Args:
        budget_min: Minimum monthly rent in CAD (default 0).
        budget_max: Maximum monthly rent in CAD (default 5000).
        bedrooms: Number of bedrooms (0=studio, 1, 2, 3+). None for any.
        neighborhood: Optional neighborhood filter (e.g., "Centretown", "Westboro").
        pet_friendly: If True, only show pet-friendly apartments.
        parking_required: If True, only show apartments with parking.
        limit: Maximum number of results to return (default 20).

    Returns:
        A dictionary with matching apartments.
    """
    log_id = "[NestFinder:search_apartments]"
    log.info(f"{log_id} Searching: ${budget_min}-${budget_max}, {bedrooms}BR")

    try:
        listings = _load_listings()
        results = []
        
        for listing in listings:
            price = listing.get("price", 0)
            beds = listing.get("bedrooms", 0)
            hood = listing.get("neighborhood", "")
            
            # Budget filter
            if price < budget_min or price > budget_max:
                continue
            
            # Bedrooms filter
            if bedrooms is not None and beds != bedrooms:
                continue
            
            # Neighborhood filter (case-insensitive partial match)
            if neighborhood and neighborhood.lower() not in hood.lower():
                continue
            
            # Pet filter
            if pet_friendly and not _is_pet_friendly(listing):
                continue
            
            # Parking filter
            if parking_required and not _has_parking(listing):
                continue
            
            apt = _listing_to_apartment(listing)
            results.append(apt)
            _apartments_cache[apt["id"]] = apt
            
            if len(results) >= limit:
                break

        log.info(f"{log_id} Found {len(results)} matching apartments")
        
        return {
            "status": "success",
            "search_criteria": {
                "budget_min": budget_min,
                "budget_max": budget_max,
                "bedrooms": bedrooms,
                "neighborhood": neighborhood,
                "pet_friendly": pet_friendly,
                "parking_required": parking_required
            },
            "total_found": len(results),
            "apartments": results
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# =============================================================================
# TOOL 2: Analyze Commute (Simulated based on neighborhood)
# =============================================================================

# Ottawa neighborhood approximate commute times to downtown (in minutes)
_COMMUTE_ESTIMATES = {
    "centretown": {"transit": 10, "driving": 8, "biking": 8, "walking": 15},
    "centretown west": {"transit": 12, "driving": 10, "biking": 10, "walking": 18},
    "byward market": {"transit": 8, "driving": 10, "biking": 6, "walking": 12},
    "sandy hill": {"transit": 15, "driving": 12, "biking": 10, "walking": 20},
    "the glebe": {"transit": 18, "driving": 12, "biking": 12, "walking": 25},
    "glebe": {"transit": 18, "driving": 12, "biking": 12, "walking": 25},
    "westboro": {"transit": 22, "driving": 15, "biking": 18, "walking": 40},
    "hintonburg": {"transit": 18, "driving": 12, "biking": 14, "walking": 30},
    "little italy": {"transit": 15, "driving": 10, "biking": 12, "walking": 22},
    "alta vista": {"transit": 25, "driving": 18, "biking": 22, "walking": 50},
    "vanier": {"transit": 20, "driving": 15, "biking": 15, "walking": 35},
    "old ottawa south": {"transit": 20, "driving": 14, "biking": 15, "walking": 30},
    "overbrook": {"transit": 22, "driving": 16, "biking": 18, "walking": 40},
    "lowertown": {"transit": 10, "driving": 8, "biking": 7, "walking": 14},
    "default": {"transit": 25, "driving": 18, "biking": 20, "walking": 45},
}


async def analyze_commute(
    apartment_id: str,
    work_address: str,
    transport_mode: str = "transit",
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze commute time from an apartment to a work address.

    Args:
        apartment_id: The apartment ID (e.g., "zumper_0_3591").
        work_address: Work address in Ottawa (e.g., "99 Bank Street, Ottawa").
        transport_mode: Preferred mode - "transit", "driving", "biking", or "walking".

    Returns:
        A dictionary with commute analysis including times and scores.
    """
    log_id = f"[NestFinder:analyze_commute:{apartment_id}]"
    log.info(f"{log_id} Analyzing commute to {work_address}")

    try:
        # Find apartment
        if apartment_id not in _apartments_cache:
            listings = _load_listings()
            for listing in listings:
                if listing.get("id") == apartment_id:
                    _apartments_cache[apartment_id] = _listing_to_apartment(listing)
                    break
        
        apt = _apartments_cache.get(apartment_id)
        if not apt:
            return {"status": "error", "message": f"Apartment {apartment_id} not found"}

        # Get commute estimates for neighborhood
        hood = apt.get("neighborhood", "").lower()
        commute = _COMMUTE_ESTIMATES.get(hood, _COMMUTE_ESTIMATES["default"])
        
        preferred_time = commute.get(transport_mode, commute["transit"])
        
        # Calculate score (shorter = better)
        if preferred_time <= 15:
            score = 95
        elif preferred_time <= 25:
            score = 75
        elif preferred_time <= 35:
            score = 55
        elif preferred_time <= 45:
            score = 35
        else:
            score = 20

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apt.get("title"),
            "neighborhood": apt.get("neighborhood"),
            "work_address": work_address,
            "commute_times": {
                "transit_minutes": commute["transit"],
                "driving_minutes": commute["driving"],
                "biking_minutes": commute["biking"],
                "walking_minutes": commute["walking"]
            },
            "preferred_mode": transport_mode,
            "preferred_time_minutes": preferred_time,
            "commute_score": score,
            "summary": f"{preferred_time} min by {transport_mode} from {apt.get('neighborhood')}"
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# =============================================================================
# TOOL 3: Analyze Neighborhood
# =============================================================================

_NEIGHBORHOOD_SCORES = {
    "centretown": {"safety": 70, "walkability": 90, "nightlife": 75, "quiet": 50},
    "centretown west": {"safety": 72, "walkability": 85, "nightlife": 60, "quiet": 60},
    "byward market": {"safety": 60, "walkability": 95, "nightlife": 95, "quiet": 30},
    "sandy hill": {"safety": 65, "walkability": 80, "nightlife": 50, "quiet": 60},
    "the glebe": {"safety": 85, "walkability": 90, "nightlife": 70, "quiet": 70},
    "glebe": {"safety": 85, "walkability": 90, "nightlife": 70, "quiet": 70},
    "westboro": {"safety": 88, "walkability": 85, "nightlife": 65, "quiet": 75},
    "hintonburg": {"safety": 75, "walkability": 82, "nightlife": 70, "quiet": 60},
    "little italy": {"safety": 78, "walkability": 85, "nightlife": 80, "quiet": 55},
    "alta vista": {"safety": 90, "walkability": 60, "nightlife": 30, "quiet": 90},
    "vanier": {"safety": 55, "walkability": 70, "nightlife": 40, "quiet": 65},
    "old ottawa south": {"safety": 88, "walkability": 75, "nightlife": 45, "quiet": 85},
    "overbrook": {"safety": 60, "walkability": 65, "nightlife": 35, "quiet": 70},
    "lowertown": {"safety": 62, "walkability": 88, "nightlife": 80, "quiet": 45},
    "default": {"safety": 70, "walkability": 70, "nightlife": 50, "quiet": 70},
}


async def analyze_neighborhood(
    apartment_id: str,
    priorities: Optional[List[str]] = None,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze the neighborhood of an apartment.

    Args:
        apartment_id: The apartment ID.
        priorities: User priorities like ["safe_area", "walkable", "nightlife", "quiet_area"].

    Returns:
        A dictionary with neighborhood analysis.
    """
    log_id = f"[NestFinder:analyze_neighborhood:{apartment_id}]"
    
    if priorities is None:
        priorities = ["safe_area", "walkable"]

    try:
        apt = _apartments_cache.get(apartment_id)
        if not apt:
            listings = _load_listings()
            for listing in listings:
                if listing.get("id") == apartment_id:
                    apt = _listing_to_apartment(listing)
                    _apartments_cache[apartment_id] = apt
                    break
        
        if not apt:
            return {"status": "error", "message": f"Apartment {apartment_id} not found"}

        hood = apt.get("neighborhood", "").lower()
        scores = _NEIGHBORHOOD_SCORES.get(hood, _NEIGHBORHOOD_SCORES["default"])
        
        # Calculate overall score based on priorities
        weights = {"safety": 0.25, "walkability": 0.25, "nightlife": 0.25, "quiet": 0.25}
        if "safe_area" in priorities:
            weights["safety"] = 0.4
        if "walkable" in priorities:
            weights["walkability"] = 0.4
        if "nightlife" in priorities:
            weights["nightlife"] = 0.4
        if "quiet_area" in priorities:
            weights["quiet"] = 0.4
        
        # Normalize weights
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        overall = int(
            scores["safety"] * weights["safety"] +
            scores["walkability"] * weights["walkability"] +
            scores["nightlife"] * weights["nightlife"] +
            scores["quiet"] * weights["quiet"]
        )

        # Safety rating
        safety = scores["safety"]
        if safety >= 85:
            safety_rating = "very safe"
        elif safety >= 70:
            safety_rating = "safe"
        elif safety >= 55:
            safety_rating = "moderate"
        else:
            safety_rating = "use caution"

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apt.get("title"),
            "neighborhood": apt.get("neighborhood"),
            "scores": {
                "safety_score": scores["safety"],
                "safety_rating": safety_rating,
                "walkability_score": scores["walkability"],
                "nightlife_score": scores["nightlife"],
                "quiet_score": scores["quiet"],
                "overall_score": overall
            },
            "summary": f"{apt.get('neighborhood')} - {safety_rating}, walkability {scores['walkability']}/100"
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# =============================================================================
# TOOL 4: Analyze Budget
# =============================================================================

# Ottawa market averages by bedroom count
_MARKET_AVERAGES = {
    0: 1450,  # Studio
    1: 1750,  # 1BR
    2: 2200,  # 2BR
    3: 2800,  # 3BR
}


async def analyze_budget(
    apartment_id: str,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze if an apartment price is a good deal compared to market rates.

    Args:
        apartment_id: The apartment ID.

    Returns:
        A dictionary with budget analysis including market comparison.
    """
    log_id = f"[NestFinder:analyze_budget:{apartment_id}]"

    try:
        apt = _apartments_cache.get(apartment_id)
        if not apt:
            listings = _load_listings()
            for listing in listings:
                if listing.get("id") == apartment_id:
                    apt = _listing_to_apartment(listing)
                    _apartments_cache[apartment_id] = apt
                    break
        
        if not apt:
            return {"status": "error", "message": f"Apartment {apartment_id} not found"}

        price = apt.get("price", 0)
        bedrooms = apt.get("bedrooms", 1)
        sqft = apt.get("sqft")
        
        market_avg = _MARKET_AVERAGES.get(bedrooms, 2000)
        difference = price - market_avg
        diff_percent = round((difference / market_avg) * 100, 1)
        
        # Score (lower price = better score)
        if diff_percent <= -15:
            score = 95
            verdict = "excellent deal"
        elif diff_percent <= -5:
            score = 80
            verdict = "good deal"
        elif diff_percent <= 5:
            score = 65
            verdict = "at market rate"
        elif diff_percent <= 15:
            score = 45
            verdict = "slightly above market"
        else:
            score = 25
            verdict = "above market"

        is_good_deal = diff_percent <= 0

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apt.get("title"),
            "neighborhood": apt.get("neighborhood"),
            "pricing": {
                "monthly_rent": price,
                "market_average": market_avg,
                "difference": difference,
                "difference_percent": diff_percent,
                "price_per_sqft": round(price / sqft, 2) if sqft else None
            },
            "budget_score": score,
            "is_good_deal": is_good_deal,
            "summary": f"${price}/mo - {verdict} ({diff_percent:+.1f}% vs market)"
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# =============================================================================
# TOOL 5: Get Full Recommendation
# =============================================================================

async def get_apartment_recommendation(
    apartment_id: str,
    work_address: str,
    priorities: Optional[List[str]] = None,
    transport_mode: str = "transit",
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get a complete recommendation for an apartment including all analyses.

    Args:
        apartment_id: The apartment ID.
        work_address: Work address for commute calculation.
        priorities: User priorities like ["short_commute", "safe_area", "walkable"].
        transport_mode: Preferred commute mode.

    Returns:
        A complete recommendation with all scores and a final verdict.
    """
    log_id = f"[NestFinder:get_recommendation:{apartment_id}]"
    
    if priorities is None:
        priorities = ["short_commute", "safe_area"]

    try:
        # Run all analyses
        commute = await analyze_commute(apartment_id, work_address, transport_mode)
        neighborhood = await analyze_neighborhood(apartment_id, priorities)
        budget = await analyze_budget(apartment_id)

        if commute.get("status") == "error":
            return commute

        apt = _apartments_cache.get(apartment_id)
        
        # Extract scores
        commute_score = commute.get("commute_score", 50)
        neighborhood_score = neighborhood.get("scores", {}).get("overall_score", 50)
        budget_score = budget.get("budget_score", 50)

        # Calculate overall score with priority weighting
        weights = {"commute": 0.33, "neighborhood": 0.33, "budget": 0.34}
        if "short_commute" in priorities:
            weights = {"commute": 0.45, "neighborhood": 0.30, "budget": 0.25}
        elif "safe_area" in priorities:
            weights = {"commute": 0.25, "neighborhood": 0.45, "budget": 0.30}
        elif "low_price" in priorities:
            weights = {"commute": 0.25, "neighborhood": 0.25, "budget": 0.50}

        overall_score = int(
            commute_score * weights["commute"] +
            neighborhood_score * weights["neighborhood"] +
            budget_score * weights["budget"]
        )

        # Generate pros and cons
        pros = []
        cons = []
        
        if commute_score >= 70:
            pros.append(f"Great commute ({commute.get('preferred_time_minutes')} min)")
        elif commute_score < 50:
            cons.append("Longer commute time")
        
        if neighborhood_score >= 70:
            pros.append(f"Excellent neighborhood")
        elif neighborhood_score < 50:
            cons.append("Neighborhood concerns")
        
        if budget.get("is_good_deal"):
            pros.append(f"Good value ({budget.get('summary')})")
        elif budget_score < 50:
            cons.append("Above market price")
        
        if apt.get("pet_friendly"):
            pros.append("Pet-friendly")
        if apt.get("parking_included"):
            pros.append("Parking included")
        if apt.get("laundry_type") == "in_unit":
            pros.append("In-unit laundry")

        # Verdict
        if overall_score >= 80:
            verdict = "Highly Recommended"
        elif overall_score >= 65:
            verdict = "Recommended"
        elif overall_score >= 50:
            verdict = "Worth Considering"
        else:
            verdict = "May Not Be the Best Fit"

        return {
            "status": "success",
            "apartment": apt,
            "analysis": {
                "commute": commute,
                "neighborhood": neighborhood,
                "budget": budget
            },
            "scores": {
                "commute_score": commute_score,
                "neighborhood_score": neighborhood_score,
                "budget_score": budget_score,
                "overall_score": overall_score
            },
            "pros": pros,
            "cons": cons,
            "verdict": verdict,
            "summary": f"{apt.get('title')} - {verdict} (Score: {overall_score}/100)"
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}