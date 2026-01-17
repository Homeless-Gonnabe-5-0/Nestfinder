# test_all_agents.py - Test all 3 agents together

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from models import Apartment
from agents.commute import CommuteAgent
from agents.neighborhood import NeighborhoodAgent
from agents.budget import BudgetAgent


async def test_full_analysis():
    """Test analyzing one apartment through all agents"""
    
    print("\n" + "="*60)
    print("TESTING ALL ANALYSIS AGENTS")
    print("="*60 + "\n")
    
    # Create test apartment
    test_apt = Apartment(
        id="test_001",
        title="Modern 1BR in Centretown",
        address="180 Metcalfe Street, Unit 804",
        neighborhood="Centretown",
        price=1650,
        bedrooms=1,
        bathrooms=1.0,
        sqft=620
    )
    
    print(f"Testing: {test_apt.title}")
    print(f"   Location: {test_apt.neighborhood}")
    print(f"   Price: ${test_apt.price}/month")
    print(f"   Size: {test_apt.sqft} sqft\n")
    
    # Initialize all agents
    print("Initializing agents...")
    commute_agent = CommuteAgent()
    neighborhood_agent = NeighborhoodAgent()
    budget_agent = BudgetAgent()
    print()
    
    # Test each agent
    print("[COMMUTE] Running Analysis...")
    commute = await commute_agent.analyze(
        test_apt, 
        "99 Bank St, Ottawa", 
        "transit"
    )
    print(f"   Transit Time: {commute.transit_minutes} min")
    print(f"   Driving Time: {commute.driving_minutes} min")
    print(f"   Biking Time: {commute.biking_minutes} min")
    print(f"   Walking Time: {commute.walking_minutes} min")
    print(f"   Best Mode: {commute.best_mode} ({commute.best_time} min)")
    print(f"   Commute Score: {commute.commute_score}/100")
    print(f"   Summary: {commute.summary}\n")
    
    print("[NEIGHBORHOOD] Running Analysis...")
    neighborhood = await neighborhood_agent.analyze(
        test_apt,
        ["safe_area", "walkable"]
    )
    print(f"   Safety Score: {neighborhood.safety_score}/100 ({neighborhood.safety_rating})")
    print(f"   Walkability: {neighborhood.walkability_score}/100")
    print(f"   Nightlife: {neighborhood.nightlife_score}/100")
    print(f"   Quiet Score: {neighborhood.quiet_score}/100")
    print(f"   Groceries Nearby: {', '.join(neighborhood.grocery_nearby)}")
    print(f"   Restaurants: {neighborhood.restaurants_nearby}")
    print(f"   Parks: {neighborhood.parks_nearby}")
    print(f"   Neighborhood Score: {neighborhood.neighborhood_score}/100")
    print(f"   Summary: {neighborhood.summary}\n")
    
    print("[BUDGET] Running Analysis...")
    budget = await budget_agent.analyze(test_apt)
    print(f"   Monthly Rent: ${budget.monthly_rent}")
    print(f"   Est. Utilities: ${budget.estimated_utilities}")
    print(f"   Total Monthly: ${budget.total_monthly}")
    print(f"   Market Average: ${budget.market_average}")
    print(f"   Price Difference: ${budget.price_difference} ({budget.price_difference_percent}%)")
    if budget.price_per_sqft:
        print(f"   Price per sqft: ${budget.price_per_sqft}")
    if budget.space_value_score is not None:
        print(f"   Space Value Score: {budget.space_value_score}/100")
    print(f"   Good Deal: {'Yes' if budget.is_good_deal else 'No'}")
    print(f"   Budget Score: {budget.budget_score}/100")
    print(f"   Summary: {budget.summary}\n")
    
    # Calculate overall
    print("="*60)
    print("OVERALL RESULTS:")
    print("="*60)
    print(f"Commute Score:      {commute.commute_score}/100")
    print(f"Neighborhood Score: {neighborhood.neighborhood_score}/100")
    print(f"Budget Score:       {budget.budget_score}/100")
    if budget.space_value_score is not None:
        print(f"Space Value:        {budget.space_value_score}/100 (informational only)")
    
    overall = (commute.commute_score + neighborhood.neighborhood_score + budget.budget_score) / 3
    print(f"\nOverall Average: {overall:.1f}/100")
    print()
    

if __name__ == "__main__":
    asyncio.run(test_full_analysis())