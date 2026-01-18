# agent_interfaces.py - EVERYONE FOLLOWS THESE SIGNATURES

"""
IMPORTANT: Each agent must implement these exact method signatures.
This ensures all agents can work together.
"""

from models import Apartment, CommuteAnalysis, NeighborhoodAnalysis, BudgetAnalysis, SearchRequest, SearchResponse


# =============================================================================
# LISTING AGENT INTERFACE
# =============================================================================

class ListingAgentInterface:
    """Interface for listing agent"""
    
    async def find_listings(
        self,
        budget_min: int,
        budget_max: int,
        bedrooms: int,
        limit: int = 20
    ) -> list[Apartment]:
        """
        Find apartments matching criteria.
        
        Args:
            budget_min: Minimum monthly rent
            budget_max: Maximum monthly rent
            bedrooms: Number of bedrooms
            limit: Max results to return
            
        Returns:
            List of Apartment objects
        """
        raise NotImplementedError


# =============================================================================
# ANALYSIS AGENT INTERFACES
# =============================================================================

class CommuteAgentInterface:
    """Interface for commute agent"""
    
    async def analyze(
        self,
        apartment: Apartment,
        work_address: str,
        preferred_mode: str = "transit"
    ) -> CommuteAnalysis:
        """
        Calculate commute times from apartment to work.
        
        Args:
            apartment: The apartment to analyze
            work_address: User's work address
            preferred_mode: "transit", "driving", "biking", "walking"
            
        Returns:
            CommuteAnalysis with times and score
        """
        raise NotImplementedError


class NeighborhoodAgentInterface:
    """Interface for neighborhood agent"""
    
    async def analyze(
        self,
        apartment: Apartment,
        priorities: list[str]
    ) -> NeighborhoodAnalysis:
        """
        Evaluate the apartment's neighborhood.
        
        Args:
            apartment: The apartment to analyze
            priorities: User's priorities (to weight scoring)
            
        Returns:
            NeighborhoodAnalysis with safety, walkability, etc.
        """
        raise NotImplementedError


class BudgetAgentInterface:
    """Interface for budget agent"""
    
    async def analyze(
        self,
        apartment: Apartment
    ) -> BudgetAnalysis:
        """
        Compare apartment price to market rates.
        
        Args:
            apartment: The apartment to analyze
            
        Returns:
            BudgetAnalysis with market comparison and score
        """
        raise NotImplementedError


# =============================================================================
# COORDINATOR INTERFACE
# =============================================================================

class CoordinatorInterface:
    """Interface for coordinator agent"""
    
    async def search(
        self,
        request: SearchRequest
    ) -> SearchResponse:
        """
        Run a full apartment search.
        
        This orchestrates all agents:
        1. Call ListingAgent to get apartments
        2. Call CommuteAgent for each apartment
        3. Call NeighborhoodAgent for each apartment
        4. Call BudgetAgent for each apartment
        5. Combine scores and rank results
        
        Args:
            request: User's search preferences
            
        Returns:
            SearchResponse with ranked recommendations
        """
        raise NotImplementedError
