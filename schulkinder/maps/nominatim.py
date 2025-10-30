import os
from typing import List

import requests
from models import Location


def get_nominatim_status() -> bool:
    """Check if the internal Nominatim service is reachable."""
    NOMINATIM_PORT = os.getenv("NOMINATIM_HOST_PORT", "8080")
    url = f"http://localhost:{NOMINATIM_PORT}/status"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def search_locations(query: str) -> List[Location]:
    """Search for locations using internal Nominatim service."""

    NOMINATIM_PORT = os.getenv("NOMINATIM_HOST_PORT", "8080")
    url = f"http://localhost:{NOMINATIM_PORT}/search"

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json()
    locations = [Location(data) for data in results]
    return locations
