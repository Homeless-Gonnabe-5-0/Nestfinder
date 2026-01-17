# agents/commute.py - Commute Agent (Person 3 will improve this later)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from models import Apartment, CommuteAnalysis
from scoring import calculate_commute_score


class CommuteAgent:
    """
    Calculates commute times from apartment to work address.
    """
    
    def __init__(self):
        self.name = "CommuteAgent"
        print(f"[{self.name}] initialized")
    
    async def analyze(
        self,
        apartment: Apartment,
        work_address: str,
        preferred_mode: str = "transit"
    ) -> CommuteAnalysis:
        """
        Calculate commute times for an apartment.
        
        Returns: CommuteAnalysis object
        """
        # TODO: Person 3 will add real API calls here
        # For now, generate realistic mock times based on neighborhood
        
        downtown_neighborhoods = ["Centretown", "Byward Market", "Sandy Hill"]
        central_neighborhoods = ["The Glebe", "Hintonburg", "Little Italy", "New Edinburgh", "Old Ottawa South"]
        
        if apartment.neighborhood in downtown_neighborhoods:
            base_transit = random.randint(10, 20)
            base_driving = random.randint(8, 15)
        elif apartment.neighborhood in central_neighborhoods:
            base_transit = random.randint(20, 35)
            base_driving = random.randint(12, 22)
        else:
            base_transit = random.randint(35, 55)
            base_driving = random.randint(20, 35)
        
        transit_minutes = base_transit
        driving_minutes = base_driving
        biking_minutes = int(driving_minutes * 1.5)
        walking_minutes = int(driving_minutes * 4)
        
        times = {
            "transit": transit_minutes,
            "driving": driving_minutes,
            "biking": biking_minutes,
            "walking": walking_minutes
        }
        best_mode = min(times, key=times.get)
        best_time = times[best_mode]
        
        commute_score = calculate_commute_score(times[preferred_mode])
        
        if times[preferred_mode] <= 20:
            summary = f"{times[preferred_mode]} min by {preferred_mode} - excellent!"
        elif times[preferred_mode] <= 35:
            summary = f"{times[preferred_mode]} min by {preferred_mode} - reasonable"
        else:
            summary = f"{times[preferred_mode]} min by {preferred_mode} - longer commute"
        
        return CommuteAnalysis(
            apartment_id=apartment.id,
            transit_minutes=transit_minutes,
            driving_minutes=driving_minutes,
            biking_minutes=biking_minutes,
            walking_minutes=walking_minutes,
            best_mode=best_mode,
            best_time=best_time,
            commute_score=commute_score,
            summary=summary
        )


# Test
if __name__ == "__main__":
    import asyncio
    from models import Apartment
    
    async def test():
        agent = CommuteAgent()
        
        test_apt = Apartment(
            id="test_001",
            title="Test Apartment",
            address="123 Main St",
            neighborhood="Centretown",
            price=1800,
            bedrooms=1,
            bathrooms=1.0
        )
        
        result = await agent.analyze(test_apt, "99 Bank St, Ottawa")
        print(f"Commute Score: {result.commute_score}")
        print(f"Summary: {result.summary}")
    
    asyncio.run(test())