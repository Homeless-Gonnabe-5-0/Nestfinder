# scoring.py - SHARED FILE
# Helper functions for calculating scores

from models import Apartment


def calculate_commute_score(minutes: int, max_acceptable: int = 45) -> int:
    """
    Convert commute minutes to 0-100 score.
    Shorter commute = higher score.
    """
    if minutes <= 0:
        return 100
    if minutes >= max_acceptable * 2:
        return 0
    
    score = 100 - (minutes / (max_acceptable * 2) * 100)
    return max(0, min(100, int(score)))


def calculate_budget_score(price: int, market_average: int) -> int:
    """
    Convert price vs market to 0-100 score.
    Below market = higher score.
    """
    if market_average <= 0:
        return 50
    
    difference_percent = ((market_average - price) / market_average) * 100
    score = 70 + difference_percent
    return max(0, min(100, int(score)))


def calculate_amenity_score(apartment: Apartment, priorities: list) -> int:
    """Score how well apartment amenities match user priorities."""
    score = 50
    
    if "pet_friendly" in priorities and apartment.pet_friendly:
        score += 20
    if "parking" in priorities and apartment.parking_included:
        score += 20
    if "laundry" in priorities:
        if apartment.laundry_type == "in_unit":
            score += 20
        elif apartment.laundry_type == "in_building":
            score += 10
    if "gym" in priorities and "gym" in apartment.amenities:
        score += 15
    
    return min(100, score)


def calculate_overall_score(
    commute_score: int,
    neighborhood_score: int,
    budget_score: int,
    amenity_score: int,
    priorities: list,
    has_commute: bool = True
) -> int:
    """
    Calculate weighted overall score based on user priorities.
    
    Args:
        commute_score: Score for commute (can be None if no work address)
        neighborhood_score: Score for neighborhood
        budget_score: Score for budget/value
        amenity_score: Score for amenities
        priorities: List of user priorities
        has_commute: Whether commute should be factored in
    """
    
    if has_commute and commute_score is not None:
        # Normal case: include commute in scoring
        weights = {
            "commute": 0.25,
            "neighborhood": 0.25,
            "budget": 0.25,
            "amenities": 0.25
        }
    else:
        # No work address: redistribute weight to other factors
        weights = {
            "commute": 0.0,
            "neighborhood": 0.35,
            "budget": 0.35,
            "amenities": 0.30
        }
    
    priority_boost = 0.15
    for i, priority in enumerate(priorities[:3]):
        boost = priority_boost * (3 - i) / 3
        
        if priority == "short_commute" and has_commute:
            weights["commute"] += boost
        elif priority in ["safe_area", "walkable", "nightlife", "quiet_area"]:
            weights["neighborhood"] += boost
        elif priority == "low_price":
            weights["budget"] += boost
        elif priority in ["parking", "gym", "laundry", "pet_friendly"]:
            weights["amenities"] += boost
    
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}
    
    # Use 0 for commute if not available
    safe_commute = commute_score if (commute_score is not None and has_commute) else 0
    
    overall = (
        safe_commute * weights["commute"] +
        neighborhood_score * weights["neighborhood"] +
        budget_score * weights["budget"] +
        amenity_score * weights["amenities"]
    )
    
    return int(overall)


def generate_headline(rank: int, scores: dict, priorities: list, has_commute: bool = True) -> str:
    """Generate a catchy headline for the recommendation."""
    if rank == 1:
        return "Best Overall Match"

    # Filter out commute from consideration if no work address
    filtered_scores = scores.copy()
    if not has_commute or scores.get("commute") is None:
        filtered_scores.pop("commute", None)
    
    if not filtered_scores:
        return f"#{rank} Recommendation"
    
    best_category = max(filtered_scores, key=lambda k: filtered_scores[k] or 0)
    
    headlines = {
        "commute": "Best for Commuters",
        "neighborhood": "Best Neighborhood",
        "budget": "Best Value",
        "amenities": "Best Amenities"
    }
    
    return headlines.get(best_category, f"#{rank} Recommendation")


def generate_match_reasons(apartment: Apartment, scores: dict, priorities: list) -> list:
    """Generate reasons why this apartment matches user needs."""
    reasons = []
    
    # Only mention commute if we have a score for it
    if scores.get("commute") is not None:
        if scores.get("commute", 0) >= 80:
            reasons.append("Excellent commute time")
        elif scores.get("commute", 0) >= 60:
            reasons.append("Good commute time")
    
    if scores.get("budget", 0) >= 80:
        reasons.append("Great value for money")
    elif scores.get("budget", 0) >= 60:
        reasons.append("Reasonably priced")
    
    if scores.get("neighborhood", 0) >= 80:
        reasons.append(f"Great location in {apartment.neighborhood}")
    
    if "pet_friendly" in priorities and apartment.pet_friendly:
        reasons.append("Pet-friendly")
    
    if "parking" in priorities and apartment.parking_included:
        reasons.append("Parking included")
    
    if apartment.laundry_type == "in_unit":
        reasons.append("In-unit laundry")
    
    return reasons[:4]


def generate_concerns(apartment: Apartment, scores: dict, priorities: list) -> list:
    """Generate potential concerns about this apartment."""
    concerns = []
    
    # Only mention commute concern if we have a score for it
    if scores.get("commute") is not None and scores.get("commute", 0) < 50:
        concerns.append("Longer commute")
    
    if scores.get("budget", 0) < 50:
        concerns.append("Above market price")
    
    if scores.get("neighborhood", 0) < 50:
        concerns.append("Neighborhood may not match preferences")
    
    if "pet_friendly" in priorities and not apartment.pet_friendly:
        concerns.append("No pets allowed")
    
    if "parking" in priorities and not apartment.parking_included:
        concerns.append("No parking included")
    
    if "laundry" in priorities and apartment.laundry_type == "none":
        concerns.append("No laundry facilities")
    
    return concerns[:3]