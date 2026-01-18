import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))    

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from models import SearchRequest, SearchResponse
from agents.coordinator import CoordinatorAgent
from agents.conversation import ConversationAgent
from constants import PRIORITIES, OTTAWA_NEIGHBORHOODS, TRANSPORT_MODES, API_VERSION

class SearchRequestAPI(BaseModel):
    """API request model (what frontend sends)"""
    budget_min: int
    budget_max: int
    work_address: str
    bedrooms: int = 1
    priorities: list = ["short_commute", "low_price"]
    max_commute_minutes: int = 45
    transport_mode: str = "transit"
    # Pinned location from map (optional - takes priority over work_address)
    pinned_lat: Optional[float] = None
    pinned_lng: Optional[float] = None


class ChatRequestAPI(BaseModel):
    """Chat request model - natural language conversation"""
    message: str
    session_id: str = "default"
    # Pinned location from map (optional)
    pinned_lat: Optional[float] = None
    pinned_lng: Optional[float] = None
    # Filter preferences
    pet_friendly: Optional[bool] = None
    bedrooms_min: Optional[int] = None
    bathrooms_min: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None

app = FastAPI(
    title="NestFinder API",
    description="Smart apartment hunting for Ottawa renters",
    version=API_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

coordinator: Optional[CoordinatorAgent] = None
conversation_agent: Optional[ConversationAgent] = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents when server starts"""
    global coordinator, conversation_agent
    print("Starting NestFinder API...")
    coordinator = CoordinatorAgent()
    conversation_agent = ConversationAgent()
    print("API ready!\n")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "ok",
        "version": API_VERSION,
        "message": "Welcome to NestFinder API! Use POST /api/v1/search to find apartments."
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": API_VERSION,
        "message": "NestFinder API is running"
    }


@app.get("/api/v1/priorities")
async def get_priorities():
    """Get list of available priorities"""
    return {
        "priorities": PRIORITIES,
        "description": "Available priorities users can select"
    }


@app.get("/api/v1/neighborhoods")
async def get_neighborhoods():
    """Get list of Ottawa neighborhoods"""
    return {
        "neighborhoods": OTTAWA_NEIGHBORHOODS,
        "city": "Ottawa"
    }


@app.get("/api/v1/transport-modes")
async def get_transport_modes():
    """Get list of transport modes"""
    return {
        "modes": TRANSPORT_MODES
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequestAPI):
    """
    Natural language chat endpoint.
    
    This handles all user messages - greetings, questions, and search requests.
    The AI decides when to trigger apartment searches.
    """
    global coordinator, conversation_agent
    
    if conversation_agent is None:
        raise HTTPException(status_code=503, detail="Conversation service not ready")
    
    # Build pinned location tuple if provided
    pinned_location = None
    if request.pinned_lat is not None and request.pinned_lng is not None:
        pinned_location = (request.pinned_lat, request.pinned_lng)

    # Build filter preferences dict
    filter_prefs = {}
    if request.pet_friendly is not None:
        filter_prefs['pet_friendly'] = request.pet_friendly
    if request.bedrooms_min is not None:
        filter_prefs['bedrooms_min'] = request.bedrooms_min
    if request.bathrooms_min is not None:
        filter_prefs['bathrooms_min'] = request.bathrooms_min
    if request.price_min is not None:
        filter_prefs['price_min'] = request.price_min
    if request.price_max is not None:
        filter_prefs['price_max'] = request.price_max

    # Get AI response
    chat_result = await conversation_agent.chat(
        message=request.message,
        session_id=request.session_id,
        pinned_location=pinned_location,
        filter_preferences=filter_prefs if filter_prefs else None
    )
    
    # If AI detected search intent, run the search
    search_results = None
    if chat_result["intent"] == "search" and chat_result["search_params"]:
        try:
            params = chat_result["search_params"]
            
            # Build search request with defaults for missing params
            search_request = SearchRequest(
                budget_min=params.get("budget_min", 0),
                budget_max=params.get("budget_max", 3000),
                work_address=params.get("work_address", ""),
                bedrooms=params.get("bedrooms", 1),
                priorities=params.get("priorities", ["short_commute", "low_price"]),
                max_commute_minutes=params.get("max_commute_minutes", 45),
                transport_mode=params.get("transport_mode", "transit"),
                pinned_lat=params.get("pinned_lat"),
                pinned_lng=params.get("pinned_lng")
            )
            
            # Run search
            response = await coordinator.search(search_request)
            search_results = response.to_dict()
            
            # Generate natural response about the apartments
            chat_result["response"] = await conversation_agent.describe_apartments(
                search_results.get("recommendations", []),
                request.message,
                request.session_id
            )
            
        except Exception as e:
            print(f"Search error in chat: {e}")
            chat_result["response"] = f"I tried to search but ran into an issue. Please try again."
    
    return {
        "response": chat_result["response"],
        "intent": chat_result["intent"],
        "search_results": search_results
    }


@app.post("/api/v1/search")
async def search_apartments(request: SearchRequestAPI):
    """
    Search for apartments based on user preferences.
    
    This is the main endpoint that the frontend calls.
    """
    global coordinator
    
    if coordinator is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Validate request
    if request.budget_min < 0 or request.budget_max < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    
    if request.budget_min > request.budget_max:
        raise HTTPException(status_code=400, detail="budget_min cannot be greater than budget_max")
    
    if request.bedrooms < 0 or request.bedrooms > 5:
        raise HTTPException(status_code=400, detail="Bedrooms must be between 0 and 5")
    
    # Convert API model to internal model
    search_request = SearchRequest(
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        work_address=request.work_address,
        bedrooms=request.bedrooms,
        priorities=request.priorities,
        max_commute_minutes=request.max_commute_minutes,
        transport_mode=request.transport_mode,
        pinned_lat=request.pinned_lat,
        pinned_lng=request.pinned_lng
    )
    
    try:
        # Run search
        response = await coordinator.search(search_request)
        return response.to_dict()
    
    except Exception as e:
        print(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🏠 NestFinder API Server")
    print("="*60)
    print("Starting server at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=5001)
