import os
from typing import Dict, List, Tuple

import requests
from schulwege.models import Location


def new_location(data: Dict) -> Location:
    location = Location(
        name=data.get("name"),
        lat=float(data.get("lat")) if data.get("lat") else None,
        lon=float(data.get("lon")) if data.get("lon") else None,
        display_name=data.get("display_name"),
        city=data.get("address", {}).get("city"),
        road=data.get("address", {}).get("road"),
        postcode=data.get("address", {}).get("postcode"),
        country=data.get("address", {}).get("country"),
        place_id=int(data.get("place_id")) if data.get("place_id") else None,
        osm_id=int(data.get("osm_id")) if data.get("osm_id") else None,
        osm_type=data.get("osm_type"),
        licence=data.get("licence"),
        amenity=data.get("address", {}).get("amenity"),
        house_number=data.get("address", {}).get("house_number"),
        quarter=data.get("address", {}).get("quarter"),
        suburb=data.get("address", {}).get("suburb"),
        state=data.get("address", {}).get("state"),
        iso3166_2_lvl4=data.get("address", {}).get("ISO3166-2-lvl4"),
        place_rank=int(data.get("place_rank")) if data.get("place_rank") else None,
        importance=float(data.get("importance")) if data.get("importance") else None,
        addresstype=data.get("addresstype"),
        boundingbox=",".join(data.get("boundingbox")) if data.get("boundingbox") else None,
    )
    return location


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
    locations = [new_location(data) for data in results]
    return locations


def get_locations_from_addresses(
    addresses: List[str], limit: int = None, notif_callback=lambda msg: None
) -> Tuple[List[Location], List[str]]:
    """Parse a list of address strings into Location objects using Nominatim."""

    NOMINATIM_PORT = os.getenv("NOMINATIM_HOST_PORT", "8080")
    url = f"http://localhost:{NOMINATIM_PORT}/search"

    locations = []
    errors = []
    for i, address in enumerate(addresses):
        notif_callback(f"Verarbeite Adresse {i + 1}/{len(addresses)} ({address[:50]}...)")
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        if results:
            location = new_location(results[0])
            locations.append(location)
        else:
            errors.append(address)
        if limit and len(locations) >= limit:
            break
    return locations, errors
