# agents/budget.py - Budget Agent (Person 3 will improve this later)

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment, BudgetAnalysis
from scoring import calculate_budget_score


class BudgetAgent:
    """
    Compares apartment price to market rates.
    """
    
    def __init__(self):
        self.name = "BudgetAgent"
        print(f"[{self.name}] initialized")
        
        # Mock market averages by neighborhood and bedroom count
        self.market_averages = {
            ("Centretown", 1): 1800,
            ("Centretown", 2): 2400,
            ("Byward Market", 1): 2000,
            ("Byward Market", 2): 2700,
            ("The Glebe", 1): 1900,
            ("The Glebe", 2): 2500,
            ("Westboro", 1): 2000,
            ("Westboro", 2): 2600,
            ("Hintonburg", 1): 1750,
            ("Hintonburg", 2): 2300,
            ("Sandy Hill", 1): 1600,
            ("Sandy Hill", 2): 2100,
            ("Little Italy", 1): 1700,
            ("Little Italy", 2): 2200,
            ("Vanier", 1): 1450,
            ("Vanier", 2): 1850,
            ("Alta Vista", 1): 1550,
            ("Alta Vista", 2): 2000,
            ("Old Ottawa South", 1): 1800,
            ("Old Ottawa South", 2): 2400,
            ("New Edinburgh", 1): 1850,
            ("New Edinburgh", 2): 2450,
        }
        
        self.default_average = {1: 1700, 2: 2200}
    
    async def analyze(self, apartment: Apartment) -> BudgetAnalysis:
        """
        Compare apartment price to market rates.
        
        Returns: BudgetAnalysis object
        """
        # Get market average for this neighborhood + bedroom count
        key = (apartment.neighborhood, apartment.bedrooms)
        market_average = self.market_averages.get(
            key,
            self.default_average.get(apartment.bedrooms, 1700)
        )
        
        # Calculate price difference
        price_difference = apartment.price - market_average
        price_difference_percent = (price_difference / market_average) * 100
        
        # Estimate utilities
        estimated_utilities = 100 if apartment.sqft and apartment.sqft < 700 else 150
        total_monthly = apartment.price + estimated_utilities
        
        # Calculate price per sqft AND space value score
        price_per_sqft = None
        space_value_score = None
        
        if apartment.sqft and apartment.sqft > 0:
            price_per_sqft = round(apartment.price / apartment.sqft, 2)
            
            # Calculate space value score (0-100) - INFORMATIONAL ONLY
            # Ottawa typical range: $2.00-$3.50/sqft for rentals
            if price_per_sqft <= 2.00:
                space_value_score = 100  # Excellent space value
            elif price_per_sqft <= 2.50:
                space_value_score = 85   # Good space value
            elif price_per_sqft <= 3.00:
                space_value_score = 70   # Fair space value
            elif price_per_sqft <= 3.50:
                space_value_score = 55   # Below average space value
            else:
                space_value_score = 40   # Poor space value
        
        # Determine if it's a good deal
        is_good_deal = price_difference_percent < -5
        
        # Calculate main budget score (based on price vs market only)
        budget_score = calculate_budget_score(apartment.price, market_average)
        
        # Generate summary
        if price_difference_percent <= -15:
            summary = f"Excellent deal! {abs(price_difference_percent):.0f}% below market"
        elif price_difference_percent <= -5:
            summary = f"Good value - {abs(price_difference_percent):.0f}% below market"
        elif price_difference_percent <= 5:
            summary = "At market rate"
        elif price_difference_percent <= 15:
            summary = f"Slightly above market (+{price_difference_percent:.0f}%)"
        else:
            summary = f"Premium pricing (+{price_difference_percent:.0f}% above market)"
        
        return BudgetAnalysis(
            apartment_id=apartment.id,
            monthly_rent=apartment.price,
            estimated_utilities=estimated_utilities,
            total_monthly=total_monthly,
            market_average=market_average,
            price_difference=price_difference,
            price_difference_percent=round(price_difference_percent, 1),
            price_per_sqft=price_per_sqft,
            is_good_deal=is_good_deal,
            budget_score=budget_score,
            space_value_score=space_value_score,  # NEW FIELD!
            summary=summary
        )


# Test
if __name__ == "__main__":
    import asyncio
    from models import Apartment
    
    async def test():
        agent = BudgetAgent()
        
        test_apt = Apartment(
            id="test_001",
            title="Test Apartment",
            address="123 Main St",
            neighborhood="Centretown",
            price=1650,
            bedrooms=1,
            bathrooms=1.0,
            sqft=600
        )
        
        result = await agent.analyze(test_apt)
        print(f"Budget Score: {result.budget_score}")
        print(f"Market Average: ${result.market_average}")
        print(f"Price per sqft: ${result.price_per_sqft}")
        print(f"Space Value Score: {result.space_value_score}")
        print(f"Summary: {result.summary}")
    
    asyncio.run(test())