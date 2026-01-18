# models.py - SHARED FILE (everyone has the same copy)
# These are the data structures everyone uses.

from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# Input models

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
    # Pinned location from map (takes priority over work_address for commute calculations)
    pinned_lat: Optional[float] = None
    pinned_lng: Optional[float] = None

    def to_dict(self):
        return asdict(self)
    
    def has_pinned_location(self) -> bool:
        """Check if user has pinned a location on the map"""
        return self.pinned_lat is not None and self.pinned_lng is not None
    
    def get_destination_coords(self) -> Optional[tuple]:
        """Get destination coordinates if pinned, otherwise None"""
        if self.has_pinned_location():
            return (self.pinned_lat, self.pinned_lng)
        return None


# Core apartment model

@dataclass
class Apartment:
    """A single apartment listing - OUTPUT from Listing Agent"""
    # Required fields
    id: str
    title: str
    address: str
    neighborhood: str
    price: int
    bedrooms: int
    bathrooms: float
    
    # Optional details
    sqft: Optional[int] = None
    amenities: list = field(default_factory=list)
    
    # Property features
    pet_friendly: bool = False
    parking_included: bool = False
    laundry_type: str = "none"
    
    # URLs and location
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    
    # Lease and walkability
    lease_term_months: int = 12
    near_grocery: bool = False
    near_park: bool = False
    near_school: bool = False

    def to_dict(self):
        return asdict(self)


# Analysis outputs

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
    budget_score: int = 0
    space_value_score: Optional[int] = None
    summary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class WalkabilityAnalysis:
    """OUTPUT from Walkability Agent"""
    apartment_id: str
    walkability_score: int = 0
    parks_nearby: int = 0
    schools_nearby: int = 0
    groceries_nearby: int = 0
    closest_park_name: Optional[str] = None
    closest_park_distance: Optional[int] = None
    closest_school_name: Optional[str] = None
    closest_school_distance: Optional[int] = None
    closest_grocery_name: Optional[str] = None
    closest_grocery_distance: Optional[int] = None
    summary: str = ""

    def to_dict(self):
        return asdict(self)


# Final output models

@dataclass
class Recommendation:
    """A single apartment recommendation with all scores"""
    rank: int
    apartment: Apartment
    commute: CommuteAnalysis
    neighborhood: NeighborhoodAnalysis
    budget: BudgetAnalysis
    walkability: Optional[WalkabilityAnalysis] = None
    overall_score: int = 0
    headline: str = ""
    match_reasons: list = field(default_factory=list)
    concerns: list = field(default_factory=list)

    def to_dict(self):
        result = {
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
        if self.walkability:
            result["walkability"] = self.walkability.to_dict()
        return result


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
