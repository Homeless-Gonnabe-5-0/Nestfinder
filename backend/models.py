# models.py - SHARED FILE (everyone has the same copy)
# These are the data structures everyone uses.

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# =============================================================================
# INPUT: What the user sends
# =============================================================================

@dataclass
class SearchRequest:
    """What the user submits to search for apartments"""
    budget_min: int
    budget_max: int
    work_address: str
    bedrooms: int = 1
    priorities: list = field(default_factory=lambda: ["short_commute", "low_price"])
    max_commute_minutes: int = 45
    transport_mode: str = "transit"

    def to_dict(self):
        return asdict(self)


# =============================================================================
# CORE: Apartment listing
# =============================================================================

@dataclass
class Apartment:
    """A single apartment listing - OUTPUT from Listing Agent"""
    id: str
    title: str
    address: str
    neighborhood: str
    price: int
    bedrooms: int
    bathrooms: float
    sqft: Optional[int] = None
    amenities: list = field(default_factory=list)
    pet_friendly: bool = False
    parking_included: bool = False
    laundry_type: str = "none"
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

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
    best_mode: str = "transit"
    best_time: int = 0
    commute_score: int = 0
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class NeighborhoodAnalysis:
    """OUTPUT from Neighborhood Agent"""
    apartment_id: str
    neighborhood_name: str
    safety_score: int = 0
    safety_rating: str = "moderate"
    walkability_score: int = 0
    nightlife_score: int = 0
    quiet_score: int = 0
    grocery_nearby: list = field(default_factory=list)
    restaurants_nearby: int = 0
    parks_nearby: int = 0
    neighborhood_score: int = 0
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class BudgetAnalysis:
    """OUTPUT from Budget Agent"""
    apartment_id: str
    monthly_rent: int
    estimated_utilities: int = 100
    total_monthly: int = 0
    market_average: int = 0
    price_difference: int = 0
    price_difference_percent: float = 0.0
    price_per_sqft: Optional[float] = None
    is_good_deal: bool = False
    budget_score: int = 0  # Based on price vs market
    space_value_score: Optional[int] = None  # NEW! Based on $/sqft
    summary: str = ""

    def to_dict(self):
        return asdict(self)


# =============================================================================
# FINAL OUTPUT: Recommendation shown to user
# =============================================================================

@dataclass
class Recommendation:
    """A single apartment recommendation with all scores"""
    rank: int
    apartment: Apartment
    commute: CommuteAnalysis
    neighborhood: NeighborhoodAnalysis
    budget: BudgetAnalysis
    overall_score: int
    headline: str
    match_reasons: list = field(default_factory=list)
    concerns: list = field(default_factory=list)

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
    recommendations: list
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