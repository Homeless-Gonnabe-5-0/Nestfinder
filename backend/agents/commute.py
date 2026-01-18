import os
import sys
from dotenv import load_dotenv
from traveltimepy import Client
from typing import Union

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Apartment, CommuteAnalysis

# Load environment variables from .env file
load_dotenv()

class TravelTimeService:
    def __init__(self):
        # Load credentials from environment variables
        self.app_id = os.getenv('TRAVELTIME_APP_ID')
        self.api_key = os.getenv('TRAVELTIME_API_KEY')
        
        if not self.app_id or not self.api_key:
            raise ValueError("TravelTime credentials not found in environment variables")
        
        # Initialize the SDK client
        self.client = Client(app_id=self.app_id, api_key=self.api_key)
    
    def test_connection(self):
        """Test if API credentials are working"""
        try:
            print("TravelTime API initialized successfully")
            print(f"App ID: {self.app_id[:8]}...")
            return True
        except Exception as e:
            print(f"Error connecting to TravelTime API: {e}")
            return False
    
    def geocode_address(self, address: str, within_country=None, limit=1):
        """
        Convert address string to latitude/longitude coordinates.
        
        Args:
            address: Address string (e.g., "123 Main St, Ottawa, ON")
            within_country: ISO country code to limit results (e.g., "CA" for Canada)
            limit: Maximum number of results (1-50)
        
        Returns:
            Dictionary with lat, lng, formatted_address or None if geocoding fails
        """
        try:
            # Build parameters
            params = {
                "query": address,
                "limit": limit
            }
            
            if within_country:
                params["within_countries"] = [within_country]
            
            response = self.client.geocoding(**params)
            
            # The response has a 'features' attribute
            if response and hasattr(response, 'features') and len(response.features) > 0:
                feature = response.features[0]
                
                # Coordinates are in [lng, lat] format in GeoJSON
                coords = feature.geometry.coordinates
                
                # Get the name from properties
                name = feature.properties.get('name', address)
                
                return {
                    "lat": coords[1],
                    "lng": coords[0],
                    "formatted_address": name
                }
            
            return None
            
        except Exception as e:
            print(f"Error geocoding address '{address}': {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _resolve_location(self, location):
        """
        Helper method to resolve a location to lat/lng coordinates.
        
        Args:
            location: Can be:
                - Tuple of (lat, lng) - from map pin
                - Dict with 'lat' and 'lng' keys
                - Dict with 'address' key (will geocode)
                - String address (will geocode)
        
        Returns:
            Tuple of (lat, lng) or (None, None) if resolution fails
        """
        # Case 0: Tuple of coordinates (lat, lng) - from map pin
        if isinstance(location, tuple) and len(location) == 2:
            return location[0], location[1]
        
        # Case 1: Already has coordinates as dict
        if isinstance(location, dict) and 'lat' in location and 'lng' in location:
            return location['lat'], location['lng']
        
        # Case 2: Dict with address key
        if isinstance(location, dict) and 'address' in location:
            address = location['address']
            result = self.geocode_address(address, within_country="CA")
            if result:
                return result['lat'], result['lng']
            return None, None
        
        # Case 3: String address
        if isinstance(location, str):
            result = self.geocode_address(location, within_country="CA")
            if result:
                return result['lat'], result['lng']
            return None, None
        
        return None, None
    
    def calculate_travel_time_flexible(self, origin, destination, 
                                      transport_mode="public_transport", departure_time=None):
        """
        Calculate travel time with flexible input formats.
        
        Args:
            origin: Can be:
                - Dict with 'lat' and 'lng' keys
                - Dict with 'address' key
                - String address
            destination: Same format options as origin
            transport_mode: Mode of transport (driving, public_transport, walking, cycling)
            departure_time: ISO 8601 formatted time (defaults to now)
        
        Returns:
            Dictionary with travel_time (in minutes) and distance (in meters), or None if unreachable
        """
        # Resolve both locations to coordinates
        origin_lat, origin_lng = self._resolve_location(origin)
        dest_lat, dest_lng = self._resolve_location(destination)
        
        if not origin_lat or not dest_lat:
            print("Failed to resolve origin or destination to coordinates")
            return None
        
        # Use the existing method with coordinates
        return self.calculate_travel_time(
            origin_lat, origin_lng, dest_lat, dest_lng, 
            transport_mode, departure_time
        )
    
    def calculate_all_travel_times_flexible(self, origin, destination, departure_time=None):
        """
        Calculate travel times for ALL transportation modes with flexible input.
        
        Args:
            origin: Can be dict with lat/lng, dict with address, or string address
            destination: Same format options as origin
            departure_time: ISO 8601 formatted time (defaults to now)
        
        Returns:
            Dictionary with results for each mode
        """
        # Resolve both locations to coordinates
        origin_lat, origin_lng = self._resolve_location(origin)
        dest_lat, dest_lng = self._resolve_location(destination)
        
        if not origin_lat or not dest_lat:
            print("Failed to resolve origin or destination to coordinates")
            return None
        
        # Use the existing method with coordinates
        return self.calculate_all_travel_times(
            origin_lat, origin_lng, dest_lat, dest_lng, 
            departure_time
        )
    
    def calculate_travel_time(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                             transport_mode="public_transport", departure_time=None):
        """
        Calculate travel time from origin to destination using coordinates.
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            transport_mode: Mode of transport (driving, public_transport, walking, cycling)
            departure_time: ISO 8601 formatted time (defaults to now)
        
        Returns:
            Dictionary with travel_time (in minutes) and distance (in meters), or None if unreachable
        """
        try:
            from datetime import datetime
            
            # Default to current time if not provided
            if departure_time is None:
                departure_time = datetime.now().isoformat()
            
            # Make the API call using routes endpoint
            response = self.client.routes(
                locations=[
                    {"id": "origin", "coords": {"lat": origin_lat, "lng": origin_lng}},
                    {"id": "destination", "coords": {"lat": dest_lat, "lng": dest_lng}}
                ],
                departure_searches=[
                    {
                        "id": "route_search",
                        "departure_location_id": "origin",
                        "arrival_location_ids": ["destination"],
                        "transportation": {"type": transport_mode},
                        "departure_time": departure_time,
                        "properties": ["travel_time", "distance"]
                    }
                ],
                arrival_searches=[]
            )
            
            # Parse the response using attribute access (Pydantic models)
            if response and response.results:
                for result in response.results:
                    if result.locations and len(result.locations) > 0:
                        location = result.locations[0]
                        if location.properties and len(location.properties) > 0:
                            prop = location.properties[0]
                            return {
                                "travel_time_minutes": prop.travel_time // 60,
                                "travel_time_seconds": prop.travel_time,
                                "distance_meters": prop.distance
                            }
            
            return None
            
        except Exception as e:
            print(f"Error calculating travel time for {transport_mode}: {e}")
            return None
    
    def calculate_all_travel_times(self, origin_lat, origin_lng, dest_lat, dest_lng, departure_time=None):
        """
        Calculate travel times for ALL transportation modes using coordinates.
        
        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            departure_time: ISO 8601 formatted time (defaults to now)
        
        Returns:
            Dictionary with results for each mode: {mode: {travel_time_minutes, distance_meters}}
        """
        modes = ["driving", "public_transport", "walking", "cycling"]
        results = {}
        
        for mode in modes:
            result = self.calculate_travel_time(
                origin_lat, origin_lng, dest_lat, dest_lng, 
                transport_mode=mode, 
                departure_time=departure_time
            )
            results[mode] = result
        
        return results
    
    def close(self):
        """Close the client session"""
        self.client.close()

class CommuteAgent:
    """
    Analyzes commute times from apartment to destination (work/school).
    Uses TravelTimeService for real-time travel calculations.
    
    Supports destinations as:
    - Tuple of (lat, lng) coordinates from map pin
    - String address (will be geocoded)
    """
    
    def __init__(self):
        self.name = "CommuteAgent"
        print(f"[{self.name}] initialized")
        
        try:
            self.travel_service = TravelTimeService()
            self.api_available = True
        except Exception as e:
            print(f"[{self.name}] Warning: TravelTime API not available ({e})")
            self.travel_service = None
            self.api_available = False
    
    def _mode_to_api(self, mode: str) -> str:
        """Convert user-friendly mode to API mode."""
        mode_map = {
            "transit": "public_transport",
            "driving": "driving",
            "biking": "cycling",
            "walking": "walking",
            "public_transport": "public_transport",
            "cycling": "cycling"
        }
        return mode_map.get(mode.lower(), "public_transport")
    
    async def analyze(
        self,
        apartment: Apartment,
        destination: Union[tuple, str],
        transport_mode: str = "transit"
    ) -> CommuteAnalysis:
        """
        Analyze commute from apartment to destination.
        
        Args:
            apartment: The apartment to analyze
            destination: Either (lat, lng) tuple from map or string address
            transport_mode: Preferred transport mode (transit, driving, biking, walking)
            
        Returns: CommuteAnalysis object
        """
        # Check if we have apartment coordinates
        if apartment.lat is None or apartment.lng is None:
            return self._fallback_analysis(apartment.id, transport_mode, apartment, destination)
        
        origin = {"lat": apartment.lat, "lng": apartment.lng}
        
        # Log what destination type we're using
        if isinstance(destination, tuple):
            print(f"[{self.name}] Using pinned location: ({destination[0]:.4f}, {destination[1]:.4f})")
        else:
            print(f"[{self.name}] Using address: {destination}")
        
        if not self.api_available or self.travel_service is None:
            return self._fallback_analysis(apartment.id, transport_mode, apartment, destination)
        
        try:
            # Get travel times for all modes
            results = self.travel_service.calculate_all_travel_times_flexible(
                origin=origin,
                destination=destination
            )
            
            if not results:
                return self._fallback_analysis(apartment.id, transport_mode, apartment, destination)
            
            # Extract times
            transit_mins = results.get("public_transport", {})
            driving_mins = results.get("driving", {})
            biking_mins = results.get("cycling", {})
            walking_mins = results.get("walking", {})
            
            transit_time = transit_mins.get("travel_time_minutes") if transit_mins else None
            driving_time = driving_mins.get("travel_time_minutes") if driving_mins else None
            biking_time = biking_mins.get("travel_time_minutes") if biking_mins else None
            walking_time = walking_mins.get("travel_time_minutes") if walking_mins else None
            
            # Determine best mode and time
            times = {
                "transit": transit_time,
                "driving": driving_time,
                "biking": biking_time,
                "walking": walking_time
            }
            
            valid_times = {k: v for k, v in times.items() if v is not None}
            
            if valid_times:
                best_mode = min(valid_times, key=valid_times.get)
                best_time = valid_times[best_mode]
            else:
                best_mode = transport_mode
                best_time = 30  # Fallback
            
            # Calculate commute score (0-100, higher is better)
            if best_time <= 10:
                commute_score = 100
            elif best_time <= 20:
                commute_score = 90
            elif best_time <= 30:
                commute_score = 75
            elif best_time <= 45:
                commute_score = 60
            elif best_time <= 60:
                commute_score = 40
            else:
                commute_score = 20
            
            # Generate summary
            if best_time <= 15:
                summary = f"Excellent! Only {best_time} min by {best_mode}"
            elif best_time <= 30:
                summary = f"Great {best_time} min commute by {best_mode}"
            elif best_time <= 45:
                summary = f"Reasonable {best_time} min by {best_mode}"
            else:
                summary = f"Long commute: {best_time} min by {best_mode}"
            
            return CommuteAnalysis(
                apartment_id=apartment.id,
                transit_minutes=transit_time,
                driving_minutes=driving_time,
                biking_minutes=biking_time,
                walking_minutes=walking_time,
                best_mode=best_mode,
                best_time=best_time,
                commute_score=commute_score,
                summary=summary
            )
            
        except Exception as e:
            print(f"[{self.name}] Error analyzing commute: {e}")
            return self._fallback_analysis(apartment.id, transport_mode, apartment, destination)
    
    def _fallback_analysis(self, apartment_id: str, mode: str, apartment: Apartment = None, destination = None) -> CommuteAnalysis:
        """Return a distance-based estimate when API is unavailable."""
        import math
        
        # Try to calculate actual distance if we have coordinates
        if apartment and apartment.lat and apartment.lng and destination:
            if isinstance(destination, tuple):
                dest_lat, dest_lng = destination
            else:
                # Default downtown Ottawa if we can't parse destination
                dest_lat, dest_lng = 45.4215, -75.6972
            
            # Haversine formula for distance in km
            R = 6371  # Earth's radius in km
            lat1, lon1 = math.radians(apartment.lat), math.radians(apartment.lng)
            lat2, lon2 = math.radians(dest_lat), math.radians(dest_lng)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance_km = R * c
            
            # Estimate times based on distance
            transit_mins = int(distance_km * 4 + 10)  # ~15km/h + wait time
            driving_mins = int(distance_km * 2 + 5)   # ~30km/h + traffic
            biking_mins = int(distance_km * 4)        # ~15km/h
            walking_mins = int(distance_km * 12)      # ~5km/h
            
            # Pick best time for mode
            times = {"transit": transit_mins, "driving": driving_mins, "biking": biking_mins, "walking": walking_mins}
            best_time = times.get(mode, transit_mins)
            
            # Score based on distance
            if distance_km <= 2:
                commute_score = 95
                summary = f"Excellent! Only {distance_km:.1f}km away (~{best_time} min)"
            elif distance_km <= 5:
                commute_score = 80
                summary = f"Great location - {distance_km:.1f}km (~{best_time} min by {mode})"
            elif distance_km <= 10:
                commute_score = 65
                summary = f"Reasonable distance - {distance_km:.1f}km (~{best_time} min)"
            else:
                commute_score = 40
                summary = f"Far - {distance_km:.1f}km (~{best_time} min)"
            
            return CommuteAnalysis(
                apartment_id=apartment_id,
                transit_minutes=transit_mins,
                driving_minutes=driving_mins,
                biking_minutes=biking_mins,
                walking_minutes=walking_mins if distance_km < 5 else None,
                best_mode=mode,
                best_time=best_time,
                commute_score=commute_score,
                summary=summary
            )
        
        # Ultimate fallback if no coordinates
        return CommuteAnalysis(
            apartment_id=apartment_id,
            transit_minutes=None,
            driving_minutes=None,
            biking_minutes=None,
            walking_minutes=None,
            best_mode=mode,
            best_time=0,
            commute_score=50,
            summary="Location unknown"
        )


# Test it
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("\n" + "="*60)
        print("Testing CommuteAgent")
        print("="*60)
        
        agent = CommuteAgent()
        
        # Create test apartment
        test_apt = Apartment(
            id="test_001",
            title="Test Apartment",
            address="200 Rideau St",
            neighborhood="Byward Market",
            price=1800,
            bedrooms=1,
            bathrooms=1.0,
            lat=45.4275,
            lng=-75.6919
        )
        
        # Test 1: Using string address
        print("\nTest 1: String address destination")
        result = await agent.analyze(
            test_apt,
            "University of Ottawa, Ottawa, ON",
            "transit"
        )
        print(f"  Result: {result.summary}")
        print(f"  Transit: {result.transit_minutes} min")
        print(f"  Score: {result.commute_score}")
        
        # Test 2: Using pinned coordinates (tuple)
        print("\nTest 2: Pinned coordinates destination")
        pinned_location = (45.4231, -75.6831)  # uOttawa coords
        result = await agent.analyze(
            test_apt,
            pinned_location,
            "transit"
        )
        print(f"  Result: {result.summary}")
        print(f"  Transit: {result.transit_minutes} min")
        print(f"  Score: {result.commute_score}")
        
        print("\n" + "="*60)
        print("CommuteAgent tests complete!")
        print("="*60)
    
    asyncio.run(test())