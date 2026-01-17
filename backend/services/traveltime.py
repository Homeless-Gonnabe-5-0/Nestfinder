import os
from dotenv import load_dotenv
from traveltimepy import Client

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
                params["within_countries"] = [within_country]  # Changed to plural
            
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
    
    def calculate_travel_time(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                             transport_mode="public_transport", departure_time=None):
        """
        Calculate travel time from origin to destination
        
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
        Calculate travel times for ALL transportation modes
        
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

# Test it
if __name__ == "__main__":
    service = TravelTimeService()
    service.test_connection()
    
    # Test geocoding
    print("\nTesting geocoding...")
    result = service.geocode_address("University of Ottawa, Ottawa, ON", within_country="CA")
    if result:
        print(f"Address: {result['formatted_address']}")
        print(f"Coordinates: ({result['lat']}, {result['lng']})")
    else:
        print("Geocoding failed")
    
    # Test with all transportation modes using geocoded coordinates
    if result:
        print("\nCalculating travel times from Downtown Ottawa to uOttawa...")
        results = service.calculate_all_travel_times(
            origin_lat=45.4215,  # Downtown Ottawa
            origin_lng=-75.6972,
            dest_lat=result['lat'],
            dest_lng=result['lng']
        )
        
        print("\nTravel Times:")
        print("=" * 50)
        for mode, travel_result in results.items():
            if travel_result:
                print(f"{mode.upper()}: {travel_result['travel_time_minutes']} min ({travel_result['distance_meters']}m)")
            else:
                print(f"{mode.upper()}: Not available")
    
    service.close()