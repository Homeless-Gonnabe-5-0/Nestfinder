import os
import requests

YELLOWCAKE_API_URL = "https://api.yellowcake.dev/v1/query"
YELLOWCAKE_API_KEY = os.getenv("YELLOWCAKE_API_KEY")


def fetch_raw_listings(city: str) -> list:
    """
    Fetch raw apartment rental listings for a given city using Yellowcake API.
    Returns a list of raw listings.
    Returns [] if API fails or no data found.
    """

    if not YELLOWCAKE_API_KEY:
        print("⚠️ Yellowcake API key not found.")
        return []

    headers = {
        "Authorization": f"Bearer {YELLOWCAKE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": (
            f"Find apartment rental listings in {city}. "
            f"Include address, price, number of bedrooms, "
            f"and whether pets are allowed if available."
        ),
        "max_results": 20
    }

    try:
        response = requests.post(
            YELLOWCAKE_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print("❌ Yellowcake API error:", e)
        return []
