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
    Recommendation
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
    2. Ask ListingAgent to find apartments
    3. For each apartment, ask analysis agents to evaluate
    4. Combine scores and rank apartments
    5. Return top recommendations
    """

    def __init__(self):
        self.name = "CoordinatorAgent"
        print(f"{self.name} initialized")
        
        # Initialize other agents
        self.listing_agent = ListingAgent()
        self.commute_agent = CommuteAgent()
        self.neighborhood_agent = NeighborhoodAgent()
        self.budget_agent = BudgetAgent()

        print(f" {self.name} ready!")

    
    async def search (self, request: SearchRequest) -> SearchResponse:
        """
        Run a full apartment search.
        
        This is the main entry point for the entire system.
        
        Args:
            request: User's search preferences
            
        Returns:
            SearchResponse with ranked recommendations
        """

        search_id = str(uuid.uuid4())[:8]
        print(f"\n{'='*60}")
        print(f"🔍 {self.name}: Starting search {search_id}")
        print(f"   Budget: ${request.budget_min}-${request.budget_max}")
        print(f"   Bedrooms: {request.bedrooms}")
        print(f"   Work: {request.work_address}")
        if request.has_pinned_location():
            print(f"   📍 Pinned Location: ({request.pinned_lat:.4f}, {request.pinned_lng:.4f})")
        print(f"   Priorities: {request.priorities}")
        print(f"{'='*60}\n")

        # Step 1: Find listings
        print(f"Step 1: Finding apartments.")
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

        print(f"Step 2: Analyzing apartments.")
        recommendations = []
        
        for i, apartment in enumerate(apartments):
            print(f"Analyzing {i+1}/{len(apartments)}: {apartment.title[:40]}...")
            
            # Run all analysis agents in PARALLEL (faster!)
            # Use pinned coordinates if available, otherwise use work address
            destination = request.get_destination_coords() or request.work_address
            commute_task = self.commute_agent.analyze(
                apartment,
                destination,
                request.transport_mode
            )
            neighborhood_task = self.neighborhood_agent.analyze(
                apartment,
                request.priorities
            )
            budget_task = self.budget_agent.analyze(apartment)
            
            # Wait for all to complete
            commute, neighborhood, budget = await asyncio.gather(
                commute_task,
                neighborhood_task,
                budget_task
            )
            
            # Calculate amenity score
            amenity_score = calculate_amenity_score(apartment, request.priorities)
            
            # Calculate overall score
            overall_score = calculate_overall_score(
                commute_score=commute.commute_score,
                neighborhood_score=neighborhood.neighborhood_score,
                budget_score=budget.budget_score,
                amenity_score=amenity_score,
                priorities=request.priorities
            )
            
            # Store scores for headline generation
            scores = {
                "commute": commute.commute_score,
                "neighborhood": neighborhood.neighborhood_score,
                "budget": budget.budget_score,
                "amenities": amenity_score
            }
            
            # Create recommendation (rank will be set after sorting)
            recommendation = Recommendation(
                rank=0,  # Temporary, will update after sorting
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
        print(f"Step 3: Ranking apartments.")
        
        # Sort by overall score (highest first)
        recommendations.sort(key=lambda x: x[0].overall_score, reverse=True)
        
        # Assign ranks and headlines
        final_recommendations = []
        for rank, (rec, scores) in enumerate(recommendations, 1):
            rec.rank = rank
            rec.headline = generate_headline(rank, scores, request.priorities)
            final_recommendations.append(rec)
            
            # Print top 5
            if rank <= 5:
                print(f"   #{rank}: {rec.apartment.title[:35]} - Score: {rec.overall_score}")
        
        # Only return top 10
        final_recommendations = final_recommendations[:10]
        
        print(f"{self.name}: Search complete!")
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
    
    # Create coordinator
    coordinator = CoordinatorAgent()
    
    # Create a test search request
    request = SearchRequest(
        budget_min=1500,
        budget_max=2000,
        work_address="99 Bank Street, Ottawa, ON",
        bedrooms=1,
        priorities=["short_commute", "safe_area", "walkable"],
        max_commute_minutes=30,
        transport_mode="transit"
    )
    
    # Run search
    response = await coordinator.search(request)
    
    # Print results
    print("\n" + "="*70)
    print("📋 SEARCH RESULTS")
    print("="*70)
    print(f"Search ID: {response.search_id}")
    print(f"Total Found: {response.total_found}")
    print(f"Recommendations: {len(response.recommendations)}")
    print()
    
    for rec in response.recommendations[:5]:
        print(f"{rec.headline}")
        print(f"   {rec.apartment.title}")
        print(f"   📍 {rec.apartment.neighborhood} | 💰 ${rec.apartment.price}/mo")
        print(f"   🏆 Overall Score: {rec.overall_score}")
        print(f"   🚗 Commute: {rec.commute.summary}")
        print(f"   🏘️ Neighborhood: {rec.neighborhood.summary}")
        print(f"   💰 Budget: {rec.budget.summary}")
        print(f"   ✅ Reasons: {', '.join(rec.match_reasons[:2])}")
        if rec.concerns:
            print(f"   ⚠️ Concerns: {', '.join(rec.concerns[:2])}")
        print()
    
    print("="*70)
    print("✅ COORDINATOR TEST COMPLETE!")
    print("="*70 + "\n")
    
    return response


if __name__ == "__main__":
    asyncio.run(test_coordinator())





    
    

