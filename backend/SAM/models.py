# models.py - EVERYONE COPIES THIS FILE EXACTLY

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

# =============================================================================
# INPUT: What the user sends
# =============================================================================

@dataclass
class SearchRequest:
    """What the user submits to search for apartments"""
    budget_min: int                    # e.g., 1500
    budget_max: int                    # e.g., 2000
    work_address: str                  # e.g., "99 Bank St, Ottawa, ON"
    bedrooms: int = 1                  # e.g., 1
    priorities: list[str] = field(default_factory=lambda: ["short_commute", "low_price"])
    max_commute_minutes: int = 45      # e.g., 45
    transport_mode: str = "transit"    # "transit", "driving", "biking", "walking"
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# CORE: Apartment listing
# =============================================================================

@dataclass
class Apartment:
    """A single apartment listing - OUTPUT from Listing Agent"""
    id: str                            # e.g., "apt_001"
    title: str                         # e.g., "Bright 1BR in Centretown"
    address: str                       # e.g., "245 Laurier Ave, Unit 5"
    neighborhood: str                  # e.g., "Centretown"
    price: int                         # e.g., 1750 (monthly rent)
    bedrooms: int                      # e.g., 1
    bathrooms: float                   # e.g., 1.0
    sqft: Optional[int] = None         # e.g., 650
    amenities: list[str] = field(default_factory=list)  # e.g., ["parking", "laundry"]
    pet_friendly: bool = False
    parking_included: bool = False
    laundry_type: str = "none"         # "in_unit", "in_building", "none"
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    lat: Optional[float] = None        # e.g., 45.4215
    lng: Optional[float] = None        # e.g., -75.6972
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# ANALYSIS: Output from each analysis agent
# =============================================================================

@dataclass
class CommuteAnalysis:
    """OUTPUT from Commute Agent"""
    apartment_id: str
    transit_minutes: Optional[int] = None
    driving_minutes: Optional[int] = None
    biking_minutes: Optional[int] = None
    walking_minutes: Optional[int] = None
    best_mode: str = "transit"         # recommended transport
    best_time: int = 0                 # minutes for best mode
    commute_score: int = 0             # 0-100 (higher = shorter commute)
    summary: str = ""                  # e.g., "22 min by transit - excellent"
    
    def to_dict(self):
        return asdict(self)


@dataclass
class NeighborhoodAnalysis:
    """OUTPUT from Neighborhood Agent"""
    apartment_id: str
    neighborhood_name: str
    safety_score: int = 0              # 0-100
    safety_rating: str = "moderate"    # "excellent", "good", "moderate", "caution"
    walkability_score: int = 0         # 0-100
    nightlife_score: int = 0           # 0-100
    quiet_score: int = 0               # 0-100 (higher = quieter)
    grocery_nearby: list[str] = field(default_factory=list)
    restaurants_nearby: int = 0        # count
    parks_nearby: int = 0              # count
    neighborhood_score: int = 0        # 0-100 overall
    summary: str = ""                  # e.g., "Safe, walkable, great for families"
    
    def to_dict(self):
        return asdict(self)


@dataclass
class BudgetAnalysis:
    """OUTPUT from Budget Agent"""
    apartment_id: str
    monthly_rent: int
    estimated_utilities: int = 100     # default estimate
    total_monthly: int = 0             # rent + utilities
    market_average: int = 0            # avg for similar in area
    price_difference: int = 0          # negative = below market (good)
    price_difference_percent: float = 0.0
    price_per_sqft: Optional[float] = None
    is_good_deal: bool = False
    budget_score: int = 0              # 0-100 (higher = better value)
    summary: str = ""                  # e.g., "12% below market - great deal!"
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# FINAL OUTPUT: Recommendation shown to user
# =============================================================================

@dataclass
class Recommendation:
    """A single apartment recommendation with all scores"""
    rank: int                          # 1 = best
    apartment: Apartment
    commute: CommuteAnalysis
    neighborhood: NeighborhoodAnalysis
    budget: BudgetAnalysis
    overall_score: int                 # 0-100 weighted average
    headline: str                      # e.g., "Best Overall Match"
    match_reasons: list[str] = field(default_factory=list)  # why it matches
    concerns: list[str] = field(default_factory=list)       # potential issues
    
    def to_dict(self):
        return {
            "rank": self.rank,
            "apartment": self.apartment.to_dict(),
            "commute": self.commute.to_dict(),
            "neighborhood": self.neighborhood.to_dict(),
            "budget": self.budget.to_dict(),
            "overall_score": self.overall_score,
            "headline": self.headline,
            "match_reasons": self.match_reasons,
            "concerns": self.concerns
        }


@dataclass
class SearchResponse:
    """Final API response to frontend"""
    search_id: str
    total_found: int
    recommendations: list[Recommendation]
    search_params: SearchRequest
    searched_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "search_id": self.search_id,
            "total_found": self.total_found,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "search_params": self.search_params.to_dict(),
            "searched_at": self.searched_at
        }

# =============================================================================
# WALKABILITY ANALYSIS
# =============================================================================
@dataclass
class WalkabilityAnalysis:
    """Output from Walkability Agent"""
    apartment_id: str
    walkability_score: int = 50        # 0-100
    parks_nearby: int = 0
    schools_nearby: int = 0
    groceries_nearby: int = 0
    closest_park_name: Optional[str] = None
    closest_park_distance: Optional[int] = None  # meters
    closest_school_name: Optional[str] = None
    closest_school_distance: Optional[int] = None
    closest_grocery_name: Optional[str] = None
    closest_grocery_distance: Optional[int] = None
    summary: str = ""
    
    def to_dict(self):
        return asdict(self)
