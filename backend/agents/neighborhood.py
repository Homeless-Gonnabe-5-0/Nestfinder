# agents/neighborhood.py - Neighborhood Agent (Person 3 will improve this later)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment, NeighborhoodAnalysis


class NeighborhoodAgent:
    """
    Evaluates neighborhood safety, walkability, and amenities.
    """
    
    def __init__(self):
        self.name = "NeighborhoodAgent"
        print(f"🏘️ {self.name} initialized")
        
        # Mock neighborhood data for Ottawa
        self.neighborhood_data = {
            "Centretown": {
                "safety_score": 75,
                "safety_rating": "good",
                "walkability_score": 92,
                "nightlife_score": 85,
                "quiet_score": 40,
                "grocery_nearby": ["Farm Boy", "Loblaws", "Metro"],
                "restaurants_nearby": 150,
                "parks_nearby": 5
            },
            "Byward Market": {
                "safety_score": 65,
                "safety_rating": "moderate",
                "walkability_score": 95,
                "nightlife_score": 95,
                "quiet_score": 25,
                "grocery_nearby": ["Moulin de Provence", "Metro"],
                "restaurants_nearby": 200,
                "parks_nearby": 3
            },
            "The Glebe": {
                "safety_score": 88,
                "safety_rating": "excellent",
                "walkability_score": 85,
                "nightlife_score": 60,
                "quiet_score": 70,
                "grocery_nearby": ["Whole Foods", "Metro", "Farm Boy"],
                "restaurants_nearby": 80,
                "parks_nearby": 8
            },
            "Westboro": {
                "safety_score": 90,
                "safety_rating": "excellent",
                "walkability_score": 82,
                "nightlife_score": 55,
                "quiet_score": 75,
                "grocery_nearby": ["Superstore", "Farm Boy"],
                "restaurants_nearby": 60,
                "parks_nearby": 10
            },
            "Hintonburg": {
                "safety_score": 72,
                "safety_rating": "good",
                "walkability_score": 80,
                "nightlife_score": 70,
                "quiet_score": 55,
                "grocery_nearby": ["Parkdale Market", "Herb & Spice"],
                "restaurants_nearby": 70,
                "parks_nearby": 6
            },
            "Sandy Hill": {
                "safety_score": 70,
                "safety_rating": "good",
                "walkability_score": 78,
                "nightlife_score": 50,
                "quiet_score": 60,
                "grocery_nearby": ["Metro", "Shoppers Drug Mart"],
                "restaurants_nearby": 40,
                "parks_nearby": 5
            },
            "Little Italy": {
                "safety_score": 75,
                "safety_rating": "good",
                "walkability_score": 83,
                "nightlife_score": 75,
                "quiet_score": 50,
                "grocery_nearby": ["Nicastro's", "La Bottega"],
                "restaurants_nearby": 90,
                "parks_nearby": 4
            },
            "Vanier": {
                "safety_score": 55,
                "safety_rating": "moderate",
                "walkability_score": 65,
                "nightlife_score": 40,
                "quiet_score": 60,
                "grocery_nearby": ["Food Basics", "Walmart"],
                "restaurants_nearby": 30,
                "parks_nearby": 4
            },
            "Alta Vista": {
                "safety_score": 85,
                "safety_rating": "excellent",
                "walkability_score": 55,
                "nightlife_score": 20,
                "quiet_score": 90,
                "grocery_nearby": ["Loblaws", "Shoppers"],
                "restaurants_nearby": 20,
                "parks_nearby": 12
            },
            "Old Ottawa South": {
                "safety_score": 87,
                "safety_rating": "excellent",
                "walkability_score": 75,
                "nightlife_score": 35,
                "quiet_score": 80,
                "grocery_nearby": ["Metro"],
                "restaurants_nearby": 25,
                "parks_nearby": 7
            },
            "New Edinburgh": {
                "safety_score": 88,
                "safety_rating": "excellent",
                "walkability_score": 72,
                "nightlife_score": 30,
                "quiet_score": 85,
                "grocery_nearby": ["Metro", "Jacobsons"],
                "restaurants_nearby": 20,
                "parks_nearby": 8
            }
        }
        
        self.default_data = {
            "safety_score": 70,
            "safety_rating": "good",
            "walkability_score": 65,
            "nightlife_score": 50,
            "quiet_score": 65,
            "grocery_nearby": ["Local grocery"],
            "restaurants_nearby": 30,
            "parks_nearby": 5
        }
    
    async def analyze(
        self,
        apartment: Apartment,
        priorities: list
    ) -> NeighborhoodAnalysis:
        """
        Evaluate the apartment's neighborhood.
        
        Returns: NeighborhoodAnalysis object
        """
        data = self.neighborhood_data.get(apartment.neighborhood, self.default_data)
        
        scores = []
        scores.append(data["safety_score"])
        scores.append(data["walkability_score"])
        
        if "nightlife" in priorities:
            scores.append(data["nightlife_score"])
        if "quiet_area" in priorities:
            scores.append(data["quiet_score"])
        
        neighborhood_score = int(sum(scores) / len(scores))
        
        summaries = []
        if data["safety_score"] >= 85:
            summaries.append("Very safe area")
        elif data["safety_score"] >= 70:
            summaries.append("Generally safe")
        
        if data["walkability_score"] >= 85:
            summaries.append("highly walkable")
        
        if "nightlife" in priorities and data["nightlife_score"] >= 70:
            summaries.append("great nightlife")
        
        if "quiet_area" in priorities and data["quiet_score"] >= 75:
            summaries.append("quiet residential area")
        
        summary = ", ".join(summaries) if summaries else f"Typical {apartment.neighborhood} neighborhood"
        summary = summary.capitalize()
        
        return NeighborhoodAnalysis(
            apartment_id=apartment.id,
            neighborhood_name=apartment.neighborhood,
            safety_score=data["safety_score"],
            safety_rating=data["safety_rating"],
            walkability_score=data["walkability_score"],
            nightlife_score=data["nightlife_score"],
            quiet_score=data["quiet_score"],
            grocery_nearby=data["grocery_nearby"],
            restaurants_nearby=data["restaurants_nearby"],
            parks_nearby=data["parks_nearby"],
            neighborhood_score=neighborhood_score,
            summary=summary
        )


# Test
if __name__ == "__main__":
    import asyncio
    from models import Apartment
    
    async def test():
        agent = NeighborhoodAgent()
        
        test_apt = Apartment(
            id="test_001",
            title="Test Apartment",
            address="123 Main St",
            neighborhood="The Glebe",
            price=1800,
            bedrooms=1,
            bathrooms=1.0
        )
        
        result = await agent.analyze(test_apt, ["safe_area", "walkable"])
        print(f"Neighborhood Score: {result.neighborhood_score}")
        print(f"Safety: {result.safety_rating}")
        print(f"Summary: {result.summary}")
    
    asyncio.run(test())