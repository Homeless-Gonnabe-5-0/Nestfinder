# agents/neighborhood.py - Neighborhood Agent with Real Crime Data

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment, NeighborhoodAnalysis


class NeighborhoodAgent:
    """
    Evaluates neighborhood safety, walkability, and amenities.
    Uses real Ottawa crime data from Open Ottawa GeoJSON files.
    """
    
    def __init__(self, crime_data_path: str = None):
        self.name = "NeighborhoodAgent"
        print(f"[{self.name}] initialized")
        
        # Path to crime data folder
        if crime_data_path is None:
            # Default: look in data/crime_data relative to backend folder
            base_path = Path(__file__).parent.parent
            crime_data_path = base_path / "data" / "crime_data"
        else:
            crime_data_path = Path(crime_data_path)
        
        self.crime_data_path = crime_data_path
        
        # Crime weights (higher = more serious)
        self.crime_weights = {
            "Homicide": 10.0,
            "Shootings": 8.0,
            "Hate_Crime": 5.0,
            "Criminal_Offences": 3.0,
            "Auto_Theft": 2.0,
            "Bike_Theft": 1.0
        }
        
        # Map Open Ottawa neighborhood names to simple names
        self.neighborhood_mapping = {
            # Centretown area
            "Centretown": "Centretown",
            "West Centertown": "Centretown",
            
            # Byward Market area
            "Lowertown": "Byward Market",
            "ByWard Market": "Byward Market",
            
            # The Glebe
            "The Glebe - Dow's Lake": "The Glebe",
            "Old Ottawa South": "Old Ottawa South",
            
            # Westboro
            "Westboro": "Westboro",
            "Westboro - Hampton Park - Woodroffe North": "Westboro",
            
            # Hintonburg
            "Hintonburg - Mechanicsville": "Hintonburg",
            
            # Sandy Hill
            "Sandy Hill": "Sandy Hill",
            "Sandy Hill East": "Sandy Hill",
            
            # Little Italy
            "Little Italy - Rochester Field - Champagne": "Little Italy",
            
            # Vanier
            "Vanier - Overbrook": "Vanier",
            "Vanier North": "Vanier",
            "Vanier South": "Vanier",
            
            # Alta Vista
            "Alta Vista": "Alta Vista",
            "Alta Vista - Canterbury": "Alta Vista",
            
            # New Edinburgh
            "New Edinburgh": "New Edinburgh",
            "New Edinburgh - Lindenlea": "New Edinburgh",
            
            # Other areas
            "Carlington": "Carlington",
            "Civic Hospital-Central Park": "Civic Hospital",
            "Britannia Village": "Britannia",
            "Bells Corners West": "Bells Corners",
            "Bells Corners East": "Bells Corners"
        }
        
        # Load crime data
        self.crime_counts = self._load_crime_data()
        self.safety_scores = self._calculate_safety_scores()
        
        # Walkability and other data (still mock - would need different data source)
        self.neighborhood_amenities = {
            "Centretown": {
                "walkability_score": 92,
                "nightlife_score": 85,
                "quiet_score": 40,
                "grocery_nearby": ["Farm Boy", "Loblaws", "Metro"],
                "restaurants_nearby": 150,
                "parks_nearby": 5
            },
            "Byward Market": {
                "walkability_score": 95,
                "nightlife_score": 95,
                "quiet_score": 25,
                "grocery_nearby": ["Moulin de Provence", "Metro"],
                "restaurants_nearby": 200,
                "parks_nearby": 3
            },
            "The Glebe": {
                "walkability_score": 85,
                "nightlife_score": 60,
                "quiet_score": 70,
                "grocery_nearby": ["Whole Foods", "Metro", "Farm Boy"],
                "restaurants_nearby": 80,
                "parks_nearby": 8
            },
            "Westboro": {
                "walkability_score": 82,
                "nightlife_score": 55,
                "quiet_score": 75,
                "grocery_nearby": ["Superstore", "Farm Boy"],
                "restaurants_nearby": 60,
                "parks_nearby": 10
            },
            "Hintonburg": {
                "walkability_score": 80,
                "nightlife_score": 70,
                "quiet_score": 55,
                "grocery_nearby": ["Parkdale Market", "Herb & Spice"],
                "restaurants_nearby": 70,
                "parks_nearby": 6
            },
            "Sandy Hill": {
                "walkability_score": 78,
                "nightlife_score": 50,
                "quiet_score": 60,
                "grocery_nearby": ["Metro", "Shoppers Drug Mart"],
                "restaurants_nearby": 40,
                "parks_nearby": 5
            },
            "Little Italy": {
                "walkability_score": 83,
                "nightlife_score": 75,
                "quiet_score": 50,
                "grocery_nearby": ["Nicastro's", "La Bottega"],
                "restaurants_nearby": 90,
                "parks_nearby": 4
            },
            "Vanier": {
                "walkability_score": 65,
                "nightlife_score": 40,
                "quiet_score": 60,
                "grocery_nearby": ["Food Basics", "Walmart"],
                "restaurants_nearby": 30,
                "parks_nearby": 4
            },
            "Alta Vista": {
                "walkability_score": 55,
                "nightlife_score": 20,
                "quiet_score": 90,
                "grocery_nearby": ["Loblaws", "Shoppers"],
                "restaurants_nearby": 20,
                "parks_nearby": 12
            },
            "Old Ottawa South": {
                "walkability_score": 75,
                "nightlife_score": 35,
                "quiet_score": 80,
                "grocery_nearby": ["Metro"],
                "restaurants_nearby": 25,
                "parks_nearby": 7
            },
            "New Edinburgh": {
                "walkability_score": 72,
                "nightlife_score": 30,
                "quiet_score": 85,
                "grocery_nearby": ["Metro", "Jacobsons"],
                "restaurants_nearby": 20,
                "parks_nearby": 8
            }
        }
        
        self.default_amenities = {
            "walkability_score": 65,
            "nightlife_score": 50,
            "quiet_score": 65,
            "grocery_nearby": ["Local grocery"],
            "restaurants_nearby": 30,
            "parks_nearby": 5
        }
    
    def _load_crime_data(self) -> dict:
        """
        Load all crime GeoJSON files and count crimes per neighborhood.
        Returns dict: {neighborhood: {crime_type: count}}
        """
        crime_counts = {}
        
        for crime_type in self.crime_weights.keys():
            file_path = self.crime_data_path / f"{crime_type}.geojson"
            
            if not file_path.exists():
                print(f"[{self.name}] Warning: {file_path} not found")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    raw_neighborhood = props.get("NB_NAME_EN", "").strip()
                    
                    # Map to simple neighborhood name
                    neighborhood = self._map_neighborhood(raw_neighborhood)
                    
                    if neighborhood not in crime_counts:
                        crime_counts[neighborhood] = {}
                    
                    if crime_type not in crime_counts[neighborhood]:
                        crime_counts[neighborhood][crime_type] = 0
                    
                    crime_counts[neighborhood][crime_type] += 1
                
                print(f"[{self.name}] Loaded {crime_type}: {len(data.get('features', []))} records")
                
            except Exception as e:
                print(f"[{self.name}] Error loading {crime_type}: {e}")
        
        return crime_counts
    
    def _map_neighborhood(self, raw_name: str) -> str:
        """Map Open Ottawa neighborhood name to simple name."""
        raw_name = raw_name.strip()
        
        # Direct match
        if raw_name in self.neighborhood_mapping:
            return self.neighborhood_mapping[raw_name]
        
        # Partial match
        for key, value in self.neighborhood_mapping.items():
            if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
                return value
        
        # Check if any of our simple names are in the raw name
        simple_names = ["Centretown", "Byward", "Glebe", "Westboro", "Hintonburg",
                       "Sandy Hill", "Little Italy", "Vanier", "Alta Vista", 
                       "Old Ottawa South", "New Edinburgh"]
        for name in simple_names:
            if name.lower() in raw_name.lower():
                return name
        
        # Return cleaned version of original
        return raw_name.split(" - ")[0].strip() if " - " in raw_name else raw_name
    
    def _calculate_safety_scores(self) -> dict:
        """
        Calculate safety scores based on weighted crime counts.
        Returns dict: {neighborhood: safety_score}
        """
        safety_scores = {}
        
        # Calculate weighted crime score for each neighborhood
        weighted_scores = {}
        for neighborhood, crimes in self.crime_counts.items():
            weighted_total = 0
            for crime_type, count in crimes.items():
                weight = self.crime_weights.get(crime_type, 1.0)
                weighted_total += count * weight
            weighted_scores[neighborhood] = weighted_total
        
        if not weighted_scores:
            print(f"[{self.name}] No crime data loaded, using default scores")
            return {}
        
        # Find min and max for normalization
        max_crime = max(weighted_scores.values())
        min_crime = min(weighted_scores.values())
        
        # Convert to 0-100 safety score (inverse - more crime = lower score)
        for neighborhood, crime_score in weighted_scores.items():
            if max_crime == min_crime:
                normalized = 0.5
            else:
                # Normalize to 0-1 range
                normalized = (crime_score - min_crime) / (max_crime - min_crime)
            
            # Invert and scale to 40-95 range (no neighborhood gets 0 or 100)
            safety_score = int(95 - (normalized * 55))
            safety_scores[neighborhood] = safety_score
        
        print(f"[{self.name}] Calculated safety scores for {len(safety_scores)} neighborhoods")
        return safety_scores
    
    def _get_safety_rating(self, score: int) -> str:
        """Convert safety score to rating string."""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "moderate"
        else:
            return "caution"
    
    def get_crime_breakdown(self, neighborhood: str) -> dict:
        """Get crime breakdown for a neighborhood (for debugging/display)."""
        return self.crime_counts.get(neighborhood, {})
    
    async def analyze(
        self,
        apartment: Apartment,
        priorities: list
    ) -> NeighborhoodAnalysis:
        """
        Evaluate the apartment's neighborhood.
        
        Returns: NeighborhoodAnalysis object
        """
        neighborhood = apartment.neighborhood
        
        # Get safety score from real crime data
        safety_score = self.safety_scores.get(neighborhood, 70)
        safety_rating = self._get_safety_rating(safety_score)
        
        # Get amenity data
        amenities = self.neighborhood_amenities.get(neighborhood, self.default_amenities)
        
        # Calculate overall neighborhood score
        scores = [safety_score, amenities["walkability_score"]]
        
        if "nightlife" in priorities:
            scores.append(amenities["nightlife_score"])
        if "quiet_area" in priorities:
            scores.append(amenities["quiet_score"])
        
        neighborhood_score = int(sum(scores) / len(scores))
        
        # Build summary
        summaries = []
        if safety_score >= 85:
            summaries.append("Very safe area")
        elif safety_score >= 70:
            summaries.append("Generally safe")
        elif safety_score < 55:
            summaries.append("Higher crime area")
        
        if amenities["walkability_score"] >= 85:
            summaries.append("highly walkable")
        
        if "nightlife" in priorities and amenities["nightlife_score"] >= 70:
            summaries.append("great nightlife")
        
        if "quiet_area" in priorities and amenities["quiet_score"] >= 75:
            summaries.append("quiet residential area")
        
        summary = ", ".join(summaries) if summaries else f"Typical {neighborhood} neighborhood"
        summary = summary.capitalize()
        
        return NeighborhoodAnalysis(
            apartment_id=apartment.id,
            neighborhood_name=neighborhood,
            safety_score=safety_score,
            safety_rating=safety_rating,
            walkability_score=amenities["walkability_score"],
            nightlife_score=amenities["nightlife_score"],
            quiet_score=amenities["quiet_score"],
            grocery_nearby=amenities["grocery_nearby"],
            restaurants_nearby=amenities["restaurants_nearby"],
            parks_nearby=amenities["parks_nearby"],
            neighborhood_score=neighborhood_score,
            summary=summary
        )


# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with crime data path (adjust path as needed)
        agent = NeighborhoodAgent()
        
        # Print loaded safety scores
        print("\n=== Safety Scores from Real Crime Data ===")
        for neighborhood, score in sorted(agent.safety_scores.items(), key=lambda x: x[1], reverse=True):
            rating = agent._get_safety_rating(score)
            print(f"  {neighborhood}: {score} ({rating})")
        
        print("\n=== Testing with Sample Apartment ===")
        from models import Apartment
        
        test_apt = Apartment(
            id="test_001",
            title="Test Apartment",
            address="123 Main St",
            neighborhood="Hintonburg",
            price=1800,
            bedrooms=1,
            bathrooms=1.0
        )
        
        result = await agent.analyze(test_apt, ["safe_area", "walkable"])
        print(f"Neighborhood: {result.neighborhood_name}")
        print(f"Safety Score: {result.safety_score} ({result.safety_rating})")
        print(f"Neighborhood Score: {result.neighborhood_score}")
        print(f"Summary: {result.summary}")
        
        # Show crime breakdown
        print(f"\nCrime breakdown for Hintonburg:")
        breakdown = agent.get_crime_breakdown("Hintonburg")
        for crime_type, count in breakdown.items():
            print(f"  {crime_type}: {count}")
    
    asyncio.run(test())