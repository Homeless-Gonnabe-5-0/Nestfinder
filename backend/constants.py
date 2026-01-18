# constants.py - SHARED FILE (everyone has the same copy)
# DO NOT MODIFY without telling the team!

# =============================================================================
# CITY CONFIG
# =============================================================================
CITY = "Ottawa"
PROVINCE = "ON"
COUNTRY = "Canada"

# =============================================================================
# PRIORITY OPTIONS (what users can choose)
# =============================================================================
PRIORITIES = {
    "short_commute": "Short Commute",
    "low_price": "Low Price",
    "safe_area": "Safe Area",
    "nightlife": "Nightlife",
    "quiet_area": "Quiet Area",
    "pet_friendly": "Pet Friendly",
    "walkable": "Walkable",
    "parking": "Parking",
    "gym": "Gym Access",
    "laundry": "In-Unit Laundry"
}

# =============================================================================
# TRANSPORT MODES
# =============================================================================
TRANSPORT_MODES = {
    "transit": "Public Transit",
    "driving": "Driving",
    "biking": "Biking",
    "walking": "Walking"
}

# =============================================================================
# SAFETY RATINGS
# =============================================================================
SAFETY_RATINGS = {
    "excellent": {"label": "Excellent", "min_score": 85},
    "good": {"label": "Good", "min_score": 70},
    "moderate": {"label": "Moderate", "min_score": 50},
    "caution": {"label": "Use Caution", "min_score": 0}
}

# =============================================================================
# OTTAWA NEIGHBORHOODS
# =============================================================================
OTTAWA_NEIGHBORHOODS = [
    "Centretown",
    "Byward Market",
    "Sandy Hill",
    "The Glebe",
    "Westboro",
    "Hintonburg",
    "Little Italy",
    "Vanier",
    "Alta Vista",
    "Kanata",
    "Orleans",
    "Barrhaven",
    "Nepean",
    "Old Ottawa South",
    "New Edinburgh"
]

# =============================================================================
# SCORING WEIGHTS (default importance of each factor)
# =============================================================================
DEFAULT_WEIGHTS = {
    "commute": 0.30,
    "neighborhood": 0.25,
    "budget": 0.25,
    "amenities": 0.20
}

# =============================================================================
# API CONFIG
# =============================================================================
API_VERSION = "v1"
DEFAULT_LISTING_LIMIT = 20
MAX_LISTING_LIMIT = 50