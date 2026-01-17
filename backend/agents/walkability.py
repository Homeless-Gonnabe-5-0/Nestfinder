# agents/walkability.py - Walkability Agent

import sys
import os
import json
import math
from pathlib import Path
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment, WalkabilityAnalysis


class WalkabilityAgent:
    """
    Evaluates walkability based on proximity to parks, schools, and groceries.
    Uses real Ottawa Open Data.
    """
    
    # Walking distance thresholds (in meters)
    WALKING_DISTANCE = 800  # ~10 min walk
    CLOSE_DISTANCE = 400    # ~5 min walk
    
    def __init__(self, data_path: str = None):
        self.name = "WalkabilityAgent"
        print(f"[{self.name}] Initializing...")
        
        # Set data path
        if data_path is None:
            base_path = Path(__file__).parent.parent
            data_path = base_path / "data" / "walkability_data"
        else:
            data_path = Path(data_path)
        
        self.data_path = data_path
        
        # Load all data
        self.parks = self._load_parks()
        self.schools = self._load_schools()
        self.groceries = self._load_groceries()
        
        print(f"[{self.name}] Loaded {len(self.parks)} parks, {len(self.schools)} schools, {len(self.groceries)} groceries")
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _load_parks(self) -> List[dict]:
        """Load parks from GeoJSON file."""
        file_path = self.data_path / "Parks_and_Greenspace.geojson"
        
        if not file_path.exists():
            print(f"[{self.name}] Warning: Parks file not found at {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            parks = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                
                # Get coordinates from properties (LATITUDE, LONGITUDE)
                lat = props.get("LATITUDE")
                lng = props.get("LONGITUDE")
                
                if lat is None or lng is None:
                    continue
                
                parks.append({
                    "name": props.get("NAME", "Unknown Park"),
                    "lat": lat,
                    "lng": lng,
                    "type": props.get("PARK_TYPE", ""),
                    "category": props.get("PARK_CATEGORY", "")
                })
            
            return parks
            
        except Exception as e:
            print(f"[{self.name}] Error loading parks: {e}")
            return []
    
    def _load_schools(self) -> List[dict]:
        """Load schools from GeoJSON file."""
        file_path = self.data_path / "Schools.geojson"
        
        if not file_path.exists():
            print(f"[{self.name}] Warning: Schools file not found at {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            schools = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                
                if len(coords) < 2:
                    continue
                
                # GeoJSON coordinates are [lng, lat]
                lng, lat = coords[0], coords[1]
                
                schools.append({
                    "name": props.get("NAME", "Unknown School"),
                    "lat": lat,
                    "lng": lng,
                    "category": props.get("CATEGORY", ""),
                    "board": props.get("BOARD", "")
                })
            
            return schools
            
        except Exception as e:
            print(f"[{self.name}] Error loading schools: {e}")
            return []
    
    def _load_groceries(self) -> List[dict]:
        """Load groceries from JSON file."""
        file_path = self.data_path / "groceries.json"
        
        if not file_path.exists():
            print(f"[{self.name}] Warning: Groceries file not found at {file_path}")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                groceries = json.load(f)
            
            # Filter out entries without coordinates
            valid_groceries = [
                g for g in groceries
                if g.get("lat") is not None and g.get("lng") is not None
            ]
            
            return valid_groceries
            
        except Exception as e:
            print(f"[{self.name}] Error loading groceries: {e}")
            return []
    
    def _find_nearby_places(
        self,
        lat: float,
        lng: float,
        places: List[dict],
        max_distance: float = None
    ) -> List[dict]:
        """Find places within walking distance, sorted by distance."""
        if max_distance is None:
            max_distance = self.WALKING_DISTANCE
        
        nearby = []
        
        for place in places:
            place_lat = place.get("lat")
            place_lng = place.get("lng")
            
            if place_lat is None or place_lng is None:
                continue
            
            distance = self._haversine_distance(lat, lng, place_lat, place_lng)
            
            if distance <= max_distance:
                nearby.append({
                    "name": place.get("name", "Unknown"),
                    "distance_m": int(distance)
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance_m"])
        
        return nearby
    
    def _calculate_score(
        self,
        parks_nearby: List[dict],
        schools_nearby: List[dict],
        groceries_nearby: List[dict]
    ) -> int:
        """
        Calculate walkability score (0-100) based on nearby amenities.
        
        Scoring weights:
        - Groceries: 40% (most important for daily life)
        - Parks: 35% (quality of life)
        - Schools: 25% (important for families)
        """
        
        # Grocery score (0-40 points)
        if groceries_nearby:
            closest_grocery = groceries_nearby[0]["distance_m"]
            if closest_grocery <= 300:
                grocery_score = 40
            elif closest_grocery <= 500:
                grocery_score = 35
            elif closest_grocery <= 800:
                grocery_score = 25
            else:
                grocery_score = 15
            # Bonus for multiple options
            grocery_score += min(len(groceries_nearby) - 1, 5) * 1
        else:
            grocery_score = 0
        
        # Park score (0-35 points)
        if parks_nearby:
            closest_park = parks_nearby[0]["distance_m"]
            if closest_park <= 300:
                park_score = 35
            elif closest_park <= 500:
                park_score = 28
            elif closest_park <= 800:
                park_score = 20
            else:
                park_score = 10
            # Bonus for multiple parks
            park_score += min(len(parks_nearby) - 1, 5) * 1
        else:
            park_score = 0
        
        # School score (0-25 points)
        if schools_nearby:
            closest_school = schools_nearby[0]["distance_m"]
            if closest_school <= 500:
                school_score = 25
            elif closest_school <= 800:
                school_score = 18
            else:
                school_score = 10
        else:
            school_score = 5  # Not having a school nearby isn't terrible
        
        total = grocery_score + park_score + school_score
        return min(100, max(0, total))
    
    def _generate_summary(
        self,
        score: int,
        parks_nearby: List[dict],
        schools_nearby: List[dict],
        groceries_nearby: List[dict]
    ) -> str:
        """Generate human-readable summary."""
        parts = []
        
        # Overall rating
        if score >= 85:
            parts.append("Excellent walkability")
        elif score >= 70:
            parts.append("Very walkable")
        elif score >= 55:
            parts.append("Somewhat walkable")
        elif score >= 40:
            parts.append("Car-dependent")
        else:
            parts.append("Very car-dependent")
        
        # Grocery info
        if groceries_nearby:
            closest = groceries_nearby[0]
            if closest["distance_m"] <= 400:
                parts.append(f"grocery {closest['distance_m']}m away")
            else:
                parts.append(f"nearest grocery {closest['distance_m']}m")
        else:
            parts.append("no grocery within walking distance")
        
        # Park info
        if parks_nearby:
            parts.append(f"{len(parks_nearby)} parks nearby")
        
        summary = ", ".join(parts)
        return summary.capitalize()
    
    async def analyze(self, apartment: Apartment) -> WalkabilityAnalysis:
        """
        Analyze walkability for an apartment.
        
        Args:
            apartment: Apartment object with lat/lng
        
        Returns:
            WalkabilityAnalysis object
        """
        if apartment.lat is None or apartment.lng is None:
            # Return default low score if no coordinates
            return WalkabilityAnalysis(
                apartment_id=apartment.id,
                walkability_score=50,
                parks_nearby=0,
                schools_nearby=0,
                groceries_nearby=0,
                summary="Location data unavailable"
            )
        
        # Find nearby places
        nearby_parks = self._find_nearby_places(apartment.lat, apartment.lng, self.parks)
        nearby_schools = self._find_nearby_places(apartment.lat, apartment.lng, self.schools)
        nearby_groceries = self._find_nearby_places(apartment.lat, apartment.lng, self.groceries)
        
        # Calculate score
        score = self._calculate_score(nearby_parks, nearby_schools, nearby_groceries)
        
        # Generate summary
        summary = self._generate_summary(score, nearby_parks, nearby_schools, nearby_groceries)
        
        # Build result
        result = WalkabilityAnalysis(
            apartment_id=apartment.id,
            walkability_score=score,
            parks_nearby=len(nearby_parks),
            schools_nearby=len(nearby_schools),
            groceries_nearby=len(nearby_groceries),
            summary=summary
        )
        
        # Add closest places
        if nearby_parks:
            result.closest_park_name = nearby_parks[0]["name"]
            result.closest_park_distance = nearby_parks[0]["distance_m"]
        
        if nearby_schools:
            result.closest_school_name = nearby_schools[0]["name"]
            result.closest_school_distance = nearby_schools[0]["distance_m"]
        
        if nearby_groceries:
            result.closest_grocery_name = nearby_groceries[0]["name"]
            result.closest_grocery_distance = nearby_groceries[0]["distance_m"]
        
        return result


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        agent = WalkabilityAgent()
        
        # Test with mock apartment
        test_apt = Apartment(
            id="apt_001",
            title="Test Centretown Apartment",
            address="180 Metcalfe Street",
            neighborhood="Centretown",
            price=1850,
            bedrooms=1,
            bathrooms=1.0,
            lat=45.4201,
            lng=-75.6941
        )
        
        print("=" * 60)
        print("Walkability Agent Test")
        print("=" * 60)
        
        result = await agent.analyze(test_apt)
        
        print(f"\n{test_apt.title}")
        print("-" * 40)
        print(f"Walkability Score: {result.walkability_score}/100")
        print(f"Summary: {result.summary}")
        print(f"Parks nearby: {result.parks_nearby}")
        print(f"Schools nearby: {result.schools_nearby}")
        print(f"Groceries nearby: {result.groceries_nearby}")
        
        if result.closest_grocery_name:
            print(f"Closest grocery: {result.closest_grocery_name} ({result.closest_grocery_distance}m)")
        if result.closest_park_name:
            print(f"Closest park: {result.closest_park_name} ({result.closest_park_distance}m)")
        if result.closest_school_name:
            print(f"Closest school: {result.closest_school_name} ({result.closest_school_distance}m)")
    
    asyncio.run(test())