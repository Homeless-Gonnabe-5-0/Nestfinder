"""
NestFinder Apartment Tools for SAM agents.

These tools connect to the actual NestFinder backend agents
which use real Ottawa data (crime stats, parks, schools, groceries).
"""

import logging
import sys
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add backend to path so we can import our agents
BACKEND_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# Import our real agents and models
from models import Apartment, WalkabilityAnalysis
from agents.commute import TravelTimeService
from agents.neighborhood import NeighborhoodAgent
from agents.budget import BudgetAgent
from agents.walkability import WalkabilityAgent
from data.mock_apartments import get_mock_apartments

log = logging.getLogger(__name__)

# Initialize agents once (they load data on init)
_commute_agent = None
_neighborhood_agent = None
_budget_agent = None
_walkability_agent = None


def _get_commute_agent():
    global _commute_agent
    if _commute_agent is None:
        _commute_agent = TravelTimeService()
    return _commute_agent


def _get_neighborhood_agent():
    global _neighborhood_agent
    if _neighborhood_agent is None:
        _neighborhood_agent = NeighborhoodAgent()
    return _neighborhood_agent


def _get_budget_agent():
    global _budget_agent
    if _budget_agent is None:
        _budget_agent = BudgetAgent()
    return _budget_agent


def _get_walkability_agent():
    global _walkability_agent
    if _walkability_agent is None:
        _walkability_agent = WalkabilityAgent()
    return _walkability_agent


def _apartment_to_dict(apt: Apartment) -> Dict:
    """Convert Apartment object to dictionary."""
    return {
        "id": apt.id,
        "title": apt.title,
        "address": apt.address,
        "neighborhood": apt.neighborhood,
        "price": apt.price,
        "bedrooms": apt.bedrooms,
        "bathrooms": apt.bathrooms,
        "sqft": apt.sqft,
        "amenities": apt.amenities,
        "pet_friendly": apt.pet_friendly,
        "parking_included": apt.parking_included,
        "laundry_type": apt.laundry_type,
        "lat": apt.lat,
        "lng": apt.lng,
        "image_url": apt.image_url
    }


# Store apartments in memory for lookup
_apartments_cache: Dict[str, Apartment] = {}


def _get_apartment_by_id(apartment_id: str) -> Optional[Apartment]:
    """Get apartment from cache or search for it."""
    if apartment_id in _apartments_cache:
        return _apartments_cache[apartment_id]
    
    # Search in all apartments
    all_apts = get_mock_apartments(0, 100000, 1) + get_mock_apartments(0, 100000, 2)
    for apt in all_apts:
        _apartments_cache[apt.id] = apt
        if apt.id == apartment_id:
            return apt
    return None


# =============================================================================
# TOOL 1: Search Apartments
# =============================================================================

async def search_apartments(
    budget_min: int,
    budget_max: int,
    bedrooms: int = 1,
    neighborhood: Optional[str] = None,
    pet_friendly: Optional[bool] = None,
    parking_required: Optional[bool] = None,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search for apartments in Ottawa based on criteria.

    Args:
        budget_min: Minimum monthly rent in CAD (e.g., 1500).
        budget_max: Maximum monthly rent in CAD (e.g., 2000).
        bedrooms: Number of bedrooms (1 or 2).
        neighborhood: Optional specific neighborhood to search in.
        pet_friendly: If True, only show pet-friendly apartments.
        parking_required: If True, only show apartments with parking.

    Returns:
        A dictionary with matching apartments.
    """
    log_id = "[NestFinder:search_apartments]"
    log.info(f"{log_id} Searching: ${budget_min}-${budget_max}, {bedrooms}BR")

    try:
        # Use real mock apartments function
        apartments = get_mock_apartments(
            budget_min=budget_min,
            budget_max=budget_max,
            bedrooms=bedrooms,
            pets_required=pet_friendly or False
        )
        
        # Additional filters
        results = []
        for apt in apartments:
            # Cache for later lookup
            _apartments_cache[apt.id] = apt
            
            # Neighborhood filter
            if neighborhood and apt.neighborhood.lower() != neighborhood.lower():
                continue
            
            # Parking filter
            if parking_required and not apt.parking_included:
                continue
            
            results.append(_apartment_to_dict(apt))

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
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# TOOL 2: Analyze Commute (using real TravelTimeService)
# =============================================================================

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
        apartment_id: The apartment ID (e.g., "apt_001").
        work_address: Work address in Ottawa (e.g., "99 Bank Street, Ottawa").
        transport_mode: Preferred mode - "transit", "driving", "biking", or "walking".

    Returns:
        A dictionary with commute analysis including times and scores.
    """
    log_id = f"[NestFinder:analyze_commute:{apartment_id}]"
    log.info(f"{log_id} Analyzing commute to {work_address} by {transport_mode}")

    # Map our transport modes to TravelTime API modes
    mode_mapping = {
        "transit": "public_transport",
        "driving": "driving",
        "biking": "cycling",
        "walking": "walking"
    }

    try:
        # Find the apartment
        apartment = _get_apartment_by_id(apartment_id)
        if not apartment:
            return {
                "status": "error",
                "message": f"Apartment {apartment_id} not found"
            }

        # Use real TravelTimeService
        service = _get_commute_agent()
        
        # Get all travel times
        results = service.calculate_all_travel_times_flexible(
            origin={"lat": apartment.lat, "lng": apartment.lng},
            destination=work_address
        )

        if not results:
            return {
                "status": "error",
                "message": "Could not calculate travel times"
            }

        # Extract times
        transit_minutes = results.get("public_transport", {}).get("travel_time_minutes") if results.get("public_transport") else None
        driving_minutes = results.get("driving", {}).get("travel_time_minutes") if results.get("driving") else None
        biking_minutes = results.get("cycling", {}).get("travel_time_minutes") if results.get("cycling") else None
        walking_minutes = results.get("walking", {}).get("travel_time_minutes") if results.get("walking") else None

        # Get preferred time
        api_mode = mode_mapping.get(transport_mode, "public_transport")
        preferred_result = results.get(api_mode, {})
        preferred_time = preferred_result.get("travel_time_minutes", 0) if preferred_result else 0

        # Calculate score (0-100, shorter = better)
        if preferred_time and preferred_time > 0:
            if preferred_time <= 15:
                score = 95
            elif preferred_time <= 25:
                score = 80
            elif preferred_time <= 35:
                score = 65
            elif preferred_time <= 45:
                score = 50
            else:
                score = max(10, 100 - preferred_time)
        else:
            score = 50

        # Generate summary
        if preferred_time:
            if preferred_time <= 15:
                rating = "excellent"
            elif preferred_time <= 25:
                rating = "very good"
            elif preferred_time <= 35:
                rating = "good"
            elif preferred_time <= 45:
                rating = "acceptable"
            else:
                rating = "long"
            summary = f"{preferred_time} min by {transport_mode} - {rating}"
        else:
            summary = "Could not calculate commute time"

        log.info(f"{log_id} Commute: {preferred_time} min by {transport_mode}")

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apartment.title,
            "neighborhood": apartment.neighborhood,
            "work_address": work_address,
            "commute_times": {
                "transit_minutes": transit_minutes,
                "driving_minutes": driving_minutes,
                "biking_minutes": biking_minutes,
                "walking_minutes": walking_minutes
            },
            "preferred_mode": transport_mode,
            "preferred_time_minutes": preferred_time,
            "commute_score": score,
            "summary": summary
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# TOOL 3: Analyze Neighborhood (using real NeighborhoodAgent with crime data)
# =============================================================================

async def analyze_neighborhood(
    apartment_id: str,
    priorities: Optional[List[str]] = None,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze the neighborhood of an apartment using real Ottawa crime data.

    Args:
        apartment_id: The apartment ID (e.g., "apt_001").
        priorities: User priorities like ["safe_area", "walkable", "nightlife", "quiet_area"].

    Returns:
        A dictionary with neighborhood analysis including safety (from real crime data), walkability, etc.
    """
    log_id = f"[NestFinder:analyze_neighborhood:{apartment_id}]"
    log.info(f"{log_id} Analyzing neighborhood with priorities: {priorities}")

    if priorities is None:
        priorities = ["safe_area", "walkable"]

    try:
        # Find the apartment
        apartment = _get_apartment_by_id(apartment_id)
        if not apartment:
            return {
                "status": "error",
                "message": f"Apartment {apartment_id} not found"
            }

        # Use real neighborhood agent (uses crime data!)
        agent = _get_neighborhood_agent()
        result = await agent.analyze(apartment=apartment, priorities=priorities)

        log.info(f"{log_id} Neighborhood score: {result.neighborhood_score}")

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apartment.title,
            "neighborhood": result.neighborhood_name,
            "scores": {
                "safety_score": result.safety_score,
                "safety_rating": result.safety_rating,
                "walkability_score": result.walkability_score,
                "nightlife_score": result.nightlife_score,
                "quiet_score": result.quiet_score,
                "overall_score": result.neighborhood_score
            },
            "amenities": {
                "grocery_nearby": result.grocery_nearby,
                "restaurants_nearby": result.restaurants_nearby,
                "parks_nearby": result.parks_nearby
            },
            "summary": result.summary
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# TOOL 4: Analyze Budget (using real BudgetAgent)
# =============================================================================

async def analyze_budget(
    apartment_id: str,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze if an apartment price is a good deal compared to market rates.

    Args:
        apartment_id: The apartment ID (e.g., "apt_001").

    Returns:
        A dictionary with budget analysis including market comparison.
    """
    log_id = f"[NestFinder:analyze_budget:{apartment_id}]"
    log.info(f"{log_id} Analyzing budget")

    try:
        # Find the apartment
        apartment = _get_apartment_by_id(apartment_id)
        if not apartment:
            return {
                "status": "error",
                "message": f"Apartment {apartment_id} not found"
            }

        # Use real budget agent
        agent = _get_budget_agent()
        result = await agent.analyze(apartment=apartment)

        log.info(f"{log_id} Budget score: {result.budget_score}")

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apartment.title,
            "neighborhood": apartment.neighborhood,
            "pricing": {
                "monthly_rent": result.monthly_rent,
                "market_average": result.market_average,
                "difference": result.price_difference,
                "difference_percent": result.price_difference_percent,
                "price_per_sqft": result.price_per_sqft
            },
            "budget_score": result.budget_score,
            "space_value_score": result.space_value_score,
            "is_good_deal": result.is_good_deal,
            "summary": result.summary
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# TOOL 5: Analyze Walkability (NEW - using real data!)
# =============================================================================

async def analyze_walkability(
    apartment_id: str,
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze walkability of an apartment using real Ottawa data (parks, schools, groceries).

    Args:
        apartment_id: The apartment ID (e.g., "apt_001").

    Returns:
        A dictionary with walkability analysis including nearby parks, schools, and grocery stores.
    """
    log_id = f"[NestFinder:analyze_walkability:{apartment_id}]"
    log.info(f"{log_id} Analyzing walkability")

    try:
        # Find the apartment
        apartment = _get_apartment_by_id(apartment_id)
        if not apartment:
            return {
                "status": "error",
                "message": f"Apartment {apartment_id} not found"
            }

        # Use real walkability agent (uses parks, schools, groceries data!)
        agent = _get_walkability_agent()
        result = await agent.analyze(apartment=apartment)

        log.info(f"{log_id} Walkability score: {result.walkability_score}")

        return {
            "status": "success",
            "apartment_id": apartment_id,
            "apartment_title": apartment.title,
            "walkability_score": result.walkability_score,
            "nearby_counts": {
                "parks": result.parks_nearby,
                "schools": result.schools_nearby,
                "groceries": result.groceries_nearby
            },
            "closest_places": {
                "park": {
                    "name": result.closest_park_name,
                    "distance_m": result.closest_park_distance
                } if result.closest_park_name else None,
                "school": {
                    "name": result.closest_school_name,
                    "distance_m": result.closest_school_distance
                } if result.closest_school_name else None,
                "grocery": {
                    "name": result.closest_grocery_name,
                    "distance_m": result.closest_grocery_distance
                } if result.closest_grocery_name else None
            },
            "summary": result.summary
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


# =============================================================================
# TOOL 6: Get Full Recommendation (combines all agents)
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
        apartment_id: The apartment ID (e.g., "apt_001").
        work_address: Work address for commute calculation.
        priorities: User priorities like ["safe_area", "walkable", "short_commute"].
        transport_mode: Preferred commute mode.

    Returns:
        A complete recommendation with all scores and a final verdict.
    """
    log_id = f"[NestFinder:get_recommendation:{apartment_id}]"
    log.info(f"{log_id} Generating full recommendation")

    if priorities is None:
        priorities = ["short_commute", "safe_area"]

    try:
        # Find the apartment
        apartment = _get_apartment_by_id(apartment_id)
        if not apartment:
            return {
                "status": "error",
                "message": f"Apartment {apartment_id} not found"
            }

        # Run all analyses using real agents
        commute = await analyze_commute(apartment_id, work_address, transport_mode)
        neighborhood = await analyze_neighborhood(apartment_id, priorities)
        budget = await analyze_budget(apartment_id)
        walkability = await analyze_walkability(apartment_id)

        # Extract scores
        commute_score = commute.get("commute_score", 50)
        neighborhood_score = neighborhood.get("scores", {}).get("overall_score", 50)
        budget_score = budget.get("budget_score", 50)
        walkability_score = walkability.get("walkability_score", 50)

        # Weight based on priorities
        weights = {"commute": 0.25, "neighborhood": 0.25, "budget": 0.25, "walkability": 0.25}
        if "short_commute" in priorities:
            weights = {"commute": 0.35, "neighborhood": 0.25, "budget": 0.20, "walkability": 0.20}
        elif "safe_area" in priorities:
            weights = {"commute": 0.20, "neighborhood": 0.35, "budget": 0.20, "walkability": 0.25}
        elif "walkable" in priorities:
            weights = {"commute": 0.20, "neighborhood": 0.20, "budget": 0.20, "walkability": 0.40}
        elif "low_price" in priorities:
            weights = {"commute": 0.20, "neighborhood": 0.20, "budget": 0.40, "walkability": 0.20}

        overall_score = int(
            commute_score * weights["commute"] +
            neighborhood_score * weights["neighborhood"] +
            budget_score * weights["budget"] +
            walkability_score * weights["walkability"]
        )

        # Generate pros and cons
        pros = []
        cons = []
        
        if commute_score >= 75:
            pros.append(f"Great commute ({commute.get('preferred_time_minutes', '?')} min)")
        elif commute_score < 50:
            cons.append("Longer commute time")
        
        if neighborhood_score >= 75:
            pros.append(f"Excellent neighborhood ({apartment.neighborhood})")
        elif neighborhood_score < 50:
            cons.append("Neighborhood may not match preferences")
        
        if budget.get("is_good_deal"):
            pros.append(f"Good value ({budget.get('summary', '')})")
        elif budget_score < 50:
            cons.append("Above market price")
        
        if walkability_score >= 75:
            pros.append(f"Very walkable ({walkability.get('nearby_counts', {}).get('groceries', 0)} groceries nearby)")
        elif walkability_score < 50:
            cons.append("Limited walkability")
        
        if apartment.pet_friendly:
            pros.append("Pet-friendly")
        
        if apartment.parking_included:
            pros.append("Parking included")
        
        if apartment.laundry_type == "in_unit":
            pros.append("In-unit laundry")

        # Final verdict
        if overall_score >= 80:
            verdict = "Highly Recommended"
        elif overall_score >= 65:
            verdict = "Recommended"
        elif overall_score >= 50:
            verdict = "Worth Considering"
        else:
            verdict = "May Not Be the Best Fit"

        log.info(f"{log_id} Overall score: {overall_score}, verdict: {verdict}")

        return {
            "status": "success",
            "apartment": _apartment_to_dict(apartment),
            "analysis": {
                "commute": commute,
                "neighborhood": neighborhood,
                "budget": budget,
                "walkability": walkability
            },
            "scores": {
                "commute_score": commute_score,
                "neighborhood_score": neighborhood_score,
                "budget_score": budget_score,
                "walkability_score": walkability_score,
                "overall_score": overall_score
            },
            "pros": pros,
            "cons": cons,
            "verdict": verdict,
            "summary": f"{apartment.title} - {verdict} (Score: {overall_score}/100)"
        }

    except Exception as e:
        log.error(f"{log_id} Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }