# scoring.py - EVERYONE COPIES THIS FILE EXACTLY

from models import Apartment


def calculate_commute_score(minutes: int, max_acceptable: int = 45) -> int:
    """
    Convert commute minutes to a 0-100 score.
    Shorter commute = higher score.
    
    Examples:
        0-15 min  -> 90-100
        15-30 min -> 70-90
        30-45 min -> 50-70
        45+ min   -> 0-50
    """
    if minutes <= 0:
        return 100
    if minutes >= max_acceptable * 2:
        return 0
    
    # Linear scale: 0 min = 100, max_acceptable = 50, 2x max = 0
    score = 100 - (minutes / (max_acceptable * 2) * 100)
    return max(0, min(100, int(score)))


def calculate_budget_score(price: int, market_average: int) -> int:
    """
    Convert price vs market to a 0-100 score.
    Below market = higher score.
    
    Examples:
        20% below market -> 90
        At market        -> 70
        20% above market -> 50
    """
    if market_average <= 0:
        return 50
    
    difference_percent = ((market_average - price) / market_average) * 100
    
    # Base score of 70, +1 point per percent below market, -1 per percent above
    score = 70 + difference_percent
    return max(0, min(100, int(score)))


def calculate_overall_score(
    commute_score: int,
    neighborhood_score: int,
    budget_score: int,
    amenity_score: int,
    priorities: list[str]
) -> int:
    """
    Calculate weighted overall score based on user priorities.
    
    Args:
        commute_score: 0-100
        neighborhood_score: 0-100
        budget_score: 0-100
        amenity_score: 0-100
        priorities: User's priority list (first = most important)
    
    Returns:
        Weighted average 0-100
    """
    # Start with default weights
    weights = {
        "commute": 0.25,
        "neighborhood": 0.25,
        "budget": 0.25,
        "amenities": 0.25
    }
    
    # Adjust weights based on priorities
    priority_boost = 0.15
    for i, priority in enumerate(priorities[:3]):  # Top 3 priorities
        boost = priority_boost * (3 - i) / 3  # First priority gets most boost
        
        if priority in ["short_commute"]:
            weights["commute"] += boost
        elif priority in ["safe_area", "walkable", "nightlife", "quiet_area"]:
            weights["neighborhood"] += boost
        elif priority in ["low_price"]:
            weights["budget"] += boost
        elif priority in ["parking", "gym", "laundry", "pet_friendly"]:
            weights["amenities"] += boost
    
    # Normalize weights to sum to 1
    total = sum(weights.values())
    weights = {k: v/total for k, v in weights.items()}
    
    # Calculate weighted score
    overall = (
        commute_score * weights["commute"] +
        neighborhood_score * weights["neighborhood"] +
        budget_score * weights["budget"] +
        amenity_score * weights["amenities"]
    )
    
    return int(overall)


def calculate_amenity_score(apartment: Apartment, priorities: list[str]) -> int:
    """
    Score how well apartment amenities match user priorities.
    """
    score = 50  # Base score
    
    if "pet_friendly" in priorities and apartment.pet_friendly:
        score += 20
    if "parking" in priorities and apartment.parking_included:
        score += 20
    if "laundry" in priorities and apartment.laundry_type == "in_unit":
        score += 20
    elif "laundry" in priorities and apartment.laundry_type == "in_building":
        score += 10
    if "gym" in priorities and "gym" in apartment.amenities:
        score += 15
    
    return min(100, score)
