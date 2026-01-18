"""NestFinder SAM Tools - Proxies to FastAPI Backend"""
import logging
import httpx
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

BACKEND_URL = "http://127.0.0.1:5001"

async def chat_nestfinder(
    message: str,
    session_id: str = "sam_user",
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Send user message to NestFinder backend."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                json={"message": message, "session_id": session_id}
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
    except httpx.ConnectError:
        return {"status": "error", "message": "Backend not running on port 5001"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def search_apartments(
    budget_min: int = 0,
    budget_max: int = 3000,
    bedrooms: int = 1,
    work_address: str = "",
    priorities: list = None,
    transport_mode: str = "transit",
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Direct search via backend API."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{BACKEND_URL}/api/v1/search",
                json={
                    "budget_min": budget_min,
                    "budget_max": budget_max,
                    "bedrooms": bedrooms,
                    "work_address": work_address,
                    "priorities": priorities or ["short_commute", "low_price"],
                    "transport_mode": transport_mode,
                    "max_commute_minutes": 45
                }
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
    except httpx.ConnectError:
        return {"status": "error", "message": "Backend not running on port 5001"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def get_neighborhoods(
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get Ottawa neighborhoods list."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BACKEND_URL}/api/v1/neighborhoods")
            return {"status": "success", "data": r.json()}
    except:
        return {"status": "error", "message": "Backend not available"}


async def get_priorities(
    tool_context: Optional[Any] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get available search priorities."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BACKEND_URL}/api/v1/priorities")
            return {"status": "success", "data": r.json()}
    except:
        return {"status": "error", "message": "Backend not available"}
