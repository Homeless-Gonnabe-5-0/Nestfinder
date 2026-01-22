# agents/coordinator.py - The Coordinator Agent

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import uuid

from models import (
    SearchRequest,
    SearchResponse,
    Recommendation,
    CommuteAnalysis
)
from scoring import (
    calculate_amenity_score,
    calculate_overall_score,
    generate_headline,
    generate_match_reasons,
    generate_concerns
)
from agents.listing import ListingAgent
from agents.commute import CommuteAgent
from agents.neighborhood import NeighborhoodAgent
from agents.budget import BudgetAgent


class CoordinatorAgent:
    """
    The Coordinator Agent - orchestrates all other agents.
    
    Flow:
    1. Receive search request from user
    2. Ask ListingAgent to find apartments (LIVE from Yellowcake)
    3. For each apartment, ask analysis agents to evaluate
    4. Combine scores and rank apartments
    5. Return top recommendations
    """

    def __init__(self):
        self.name = "CoordinatorAgent"
        print(f"{self.name} initialized")
        
        # Initialize agents
        self.listing_agent = ListingAgent()  # Uses Yellowcake for live data
        self.commute_agent = CommuteAgent()
        self.neighborhood_agent = NeighborhoodAgent()
        self.budget_agent = BudgetAgent()

        print(f"{self.name} ready!")

    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Run a full apartment search.
        
        Args:
            request: User's search preferences
            
        Returns:
            SearchResponse with ranked recommendations
        """

        search_id = str(uuid.uuid4())[:8]
        print(f"\n{'='*60}")
        print(f"🔍 {self.name}: Starting search {search_id}")
        print(f"   Budget: ${request.budget_min}-${request.budget_max}")
        print(f"   Bedrooms: {request.bedrooms if request.bedrooms is not None else 'Any'}")
        
        # Check if user provided work location
        has_work_location = bool(request.work_address) or request.has_pinned_location()
        
        if request.work_address:
            print(f"   Work: {request.work_address}")
        if request.has_pinned_location():
            print(f"   📍 Pinned Location: ({request.pinned_lat:.4f}, {request.pinned_lng:.4f})")
        if not has_work_location:
            print(f"   Work: Not provided (skipping commute analysis)")
            
        print(f"   Priorities: {request.priorities}")
        print(f"{'='*60}\n")

        # Step 1: Find listings using USER'S SEARCH CRITERIA
        print(f"Step 1: Finding apartments matching your criteria...")
        apartments = await self.listing_agent.find_listings(
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            bedrooms=request.bedrooms,
            limit=30
        )
        
        if not apartments:
            print(f"No apartments found!")
            return SearchResponse(
                search_id=search_id,
                total_found=0,
                recommendations=[],
                search_params=request
            )
        
        print(f"Found {len(apartments)} apartments\n")

        # Step 2: Analyze each apartment
        print(f"Step 2: Analyzing apartments...")
        recommendations = []
        
        for i, apartment in enumerate(apartments):
            print(f"  Analyzing {i+1}/{len(apartments)}: {apartment.title[:40]}...")
            
            # Only analyze commute if work location is provided
            if has_work_location:
                destination = request.get_destination_coords() or request.work_address
                commute_task = self.commute_agent.analyze(
                    apartment,
                    destination,
                    request.transport_mode
                )
            else:
                commute_task = None
            
            neighborhood_task = self.neighborhood_agent.analyze(
                apartment,
                request.priorities
            )
            budget_task = self.budget_agent.analyze(apartment)
            
            # Wait for all to complete
            if commute_task:
                commute, neighborhood, budget = await asyncio.gather(
                    commute_task,
                    neighborhood_task,
                    budget_task
                )
            else:
                # No commute analysis needed
                neighborhood, budget = await asyncio.gather(
                    neighborhood_task,
                    budget_task
                )
                # Create empty commute result
                commute = CommuteAnalysis(
                    apartment_id=apartment.id,
                    transit_minutes=None,
                    driving_minutes=None,
                    biking_minutes=None,
                    walking_minutes=None,
                    best_mode=None,
                    best_time=None,
                    commute_score=None,
                    summary=None
                )
            
            # Calculate amenity score
            amenity_score = calculate_amenity_score(apartment, request.priorities)
            
            # Calculate overall score
            overall_score = calculate_overall_score(
                commute_score=commute.commute_score,
                neighborhood_score=neighborhood.neighborhood_score,
                budget_score=budget.budget_score,
                amenity_score=amenity_score,
                priorities=request.priorities,
                has_commute=has_work_location
            )
            
            # Store scores for headline generation
            scores = {
                "commute": commute.commute_score,
                "neighborhood": neighborhood.neighborhood_score,
                "budget": budget.budget_score,
                "amenities": amenity_score
            }
            
            # Create recommendation
            recommendation = Recommendation(
                rank=0,  # Will update after sorting
                apartment=apartment,
                commute=commute,
                neighborhood=neighborhood,
                budget=budget,
                overall_score=overall_score,
                headline="",  # Will set after ranking
                match_reasons=generate_match_reasons(apartment, scores, request.priorities),
                concerns=generate_concerns(apartment, scores, request.priorities)
            )
            
            recommendations.append((recommendation, scores))

        # Step 3: Rank recommendations
        print(f"\nStep 3: Ranking apartments...")
        
        # Sort by overall score (highest first)
        recommendations.sort(key=lambda x: x[0].overall_score, reverse=True)
        
        # Assign ranks and headlines
        final_recommendations = []
        for rank, (rec, scores) in enumerate(recommendations, 1):
            rec.rank = rank
            rec.headline = generate_headline(rank, scores, request.priorities, has_commute=has_work_location)
            final_recommendations.append(rec)
            
            # Print top 5
            if rank <= 5:
                print(f"   #{rank}: {rec.apartment.title[:35]} - Score: {rec.overall_score}")
        
        # Return top 10
        final_recommendations = final_recommendations[:10]
        
        print(f"\n{self.name}: Search complete!")
        print(f"   Returning top {len(final_recommendations)} recommendations\n")
        
        return SearchResponse(
            search_id=search_id,
            total_found=len(apartments),
            recommendations=final_recommendations,
            search_params=request
        )


# Test
async def test_coordinator():
    """Test the full search flow"""
    print("\n" + "="*70)
    print("🧪 TESTING COORDINATOR AGENT")
    print("="*70 + "\n")
    
    coordinator = CoordinatorAgent()
    
    # Test 1: WITH work address
    print("\n--- TEST 1: With work address ---\n")
    request_with_work = SearchRequest(
        budget_min=1500,
        budget_max=2500,
        work_address="99 Bank Street, Ottawa, ON",
        bedrooms=1,
        priorities=["short_commute", "safe_area", "walkable"],
        max_commute_minutes=30,
        transport_mode="transit"
    )
    
    response1 = await coordinator.search(request_with_work)
    
    print("\n--- Results with work address ---")
    for rec in response1.recommendations[:3]:
        print(f"  {rec.headline}")
        print(f"    {rec.apartment.title} - ${rec.apartment.price}/mo")
        if rec.commute.summary:
            print(f"    🚗 Commute: {rec.commute.summary}")
        print()
    
    # Test 2: WITHOUT work address
    print("\n--- TEST 2: Without work address ---\n")
    request_no_work = SearchRequest(
        budget_min=1800,
        budget_max=2800,
        work_address=None,
        bedrooms=2,
        priorities=["safe_area", "parking"],
        transport_mode="transit"
    )
    
    response2 = await coordinator.search(request_no_work)
    
    print("\n--- Results without work address ---")
    for rec in response2.recommendations[:3]:
        print(f"  {rec.headline}")
        print(f"    {rec.apartment.title} - ${rec.apartment.price}/mo")
        if rec.commute.summary:
            print(f"    🚗 Commute: {rec.commute.summary}")
        else:
            print(f"    🚗 Commute: N/A (no work address provided)")
        print()
    
    print("="*70)
    print("✅ COORDINATOR TEST COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_coordinator())





    
    

