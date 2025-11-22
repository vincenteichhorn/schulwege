import os
from typing import Any, Dict, List

from schulwege.models.location import Location, new_location


def get_nominatim_url() -> str:
    """Get the Nominatim API URL from environment variables."""
    NOMINATIM_HOST = "localhost"
    NOMINATIM_PORT = os.getenv("NOMINATIM_HOST_PORT", "8080")
    return f"http://{NOMINATIM_HOST}:{NOMINATIM_PORT}"


def get_locations(query: str, limit: int = 10) -> List[Location]:
    """Get location data from Nominatim API."""
    import requests

    url = f"{get_nominatim_url()}/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "extratags": 1,
        "limit": limit,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if not data:
        return []
    return [new_location(item) for item in data]


def get_top_location_batch(queries: List[str], progress_callback=None) -> List[Location]:
    """Get the top location for each query in the list."""
    results = []
    for i, query in enumerate(queries):
        if progress_callback:
            progress_callback(i, query)
        locations = get_locations(query, limit=1)
        if locations:
            results.append(locations[0])
        else:
            results.append(None)
    return results
