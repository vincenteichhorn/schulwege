from datetime import datetime
import os
from typing import List, Tuple
import polyline
import requests
import streamlit as st
import osmnx as ox
from shapely import MultiPoint, length
from math import radians, sin, cos, sqrt, atan2

from schulwege.models import Location


def init_osmnx():

    ox.settings.use_cache = True
    cache_dir = os.getenv("CACHE_DIR", "data/cache")
    os.makedirs(cache_dir, exist_ok=True)
    ox.settings.cache_folder = cache_dir
    ox.settings.log_console = False


def get_graph_in_bbox(bbox: Tuple[float, float, float, float]):
    """Load OSMnx graph for the given bounding box.

    Args:
        bbox (tuple): (north, south, east, west) bounding box coordinates.

    Returns:
        ox.graph.Graph: The loaded OSMnx graph.
    """
    graph = ox.graph_from_bbox(bbox, network_type="all")
    return graph


@st.cache_data(
    persist="disk",
    hash_funcs={Location: lambda loc: (loc.lat, loc.lon) if loc.coordinates else loc.to_string()},
    show_spinner=False,
)
def get_graph_in_hull(locations: List[Location], buffer_meters=2000, network_type="all"):
    """Load OSMnx graph for the convex hull of the given locations.

    Args:
        locations (list[Location]): List of Location objects.
    Returns:
        ox.graph.Graph: The loaded OSMnx graph.
    """
    points = [(loc.lat, loc.lon) for loc in locations if loc.coordinates is not None]
    if not points:
        raise ValueError("No valid coordinates found in locations.")
    hull = MultiPoint([(lon, lat) for lat, lon in points]).convex_hull
    buffer_degrees = buffer_meters / 111320
    hull = hull.buffer(buffer_degrees)
    graph = ox.graph_from_polygon(hull, network_type=network_type)
    return graph


def get_tempo_streets(graph, speed_kmh: int = 50):
    edges = ox.graph_to_gdfs(graph, nodes=False)
    edges["speed_kmh"] = edges["maxspeed"].apply(
        lambda x: int(x[0]) if isinstance(x, list) and x and x[0].isdigit() else speed_kmh
    )
    tempo_edges = edges[edges["speed_kmh"] <= speed_kmh]
    return tempo_edges


def get_route(
    graph, origin_location: Location, destination_location: Location
) -> List[Tuple[float, float]]:
    """Get route between two locations using OSMnx.

    Args:
        graph (ox.graph.Graph): The OSMnx graph.
        origin_location (Location): The starting location.
        destination_location (Location): The destination location.

    Returns:
        list[tuple[float, float]]: List of (lat, lon) tuples representing the route.
    """
    origin_node = ox.distance.nearest_nodes(graph, origin_location.lon, origin_location.lat)
    destination_node = ox.distance.nearest_nodes(
        graph, destination_location.lon, destination_location.lat
    )

    route = ox.shortest_path(graph, origin_node, destination_node, weight="length")

    route_coords = [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in route]
    return route_coords


def haversine(lat1, lon1, lat2, lon2):

    R = 6371000  # Radius of the Earth in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


def filter_radius_locations(
    main_location: Location, locations: list[Location], radius_meters: float
) -> list[Location]:
    """Filter locations within a given radius from the main location. Luftlinie."""

    filtered_locations = []
    for loc in locations:
        distance = haversine(main_location.lat, main_location.lon, loc.lat, loc.lon)
        if distance <= radius_meters:
            filtered_locations.append(loc)
    return filtered_locations


def compute_routes(
    main_location: Location,
    locations: list[Location],
    network="walk",
    date: datetime = None,
    notif_callback: lambda x: None = None,
) -> Tuple[List[List[Tuple[float, float]]], List[List[str]]]:
    """Compute walking routes from main_location to each location in locations.

    Args:
        main_location (Location): The starting location.
        locations (list[Location]): List of destination locations.

    Returns:
        tuple: A tuple containing:
            - list of routes, each route is a list of (lat, lon) tuples
            - list of route specific modalities, each is a list of strings for each point of the route the specific modality it is on
    """

    if network in ["walk", "bike"]:
        all_locations = [main_location] + locations
        notif_callback(f"Lade  {network.capitalize()}-Netzwerk.")
        graph = get_graph_in_hull(all_locations, buffer_meters=2000, network_type=network)

        routes = []
        for i, loc in enumerate(locations):
            notif_callback(f"Berechne {network.capitalize()}-Route {i + 1}/{len(locations)}.")
            route = get_route(graph, main_location, loc)
            routes.append(route)

        return routes, [[network] * len(route) for route in routes]
    elif network == "oepnv":

        routes = []
        modality_descs = []
        for i, loc in enumerate(locations):
            notif_callback(f"Berechne ÖPNV-Route {i + 1}/{len(locations)}.")
            _date = date.strftime("%Y-%m-%d") if date else datetime.now().strftime("%Y-%m-%d")
            time = date.strftime("%H:%M") if date else datetime.now().strftime("%H:%M")
            route, modality_desc = get_public_transport_route(
                origin=main_location,
                destination=loc,
                date=_date,
                time=time,
                transport_modes=[
                    "BUS",
                    "TRAM",
                    "RAIL",
                    "SUBWAY",
                    "FERRY",
                    "GONDOLA",
                    "FUNICULAR",
                    "WALK",
                ],
            )
            routes.append(route)
            modality_descs.append(modality_desc)
        return routes, modality_descs
    else:
        raise ValueError(f"Unsupported network type: {network}")


def get_public_transport_route(
    origin: Location,
    destination: Location,
    date: str,
    time: str,
    transport_modes: list,
    return_points_of: list = None,
):

    from_lat = origin.lat
    from_lon = origin.lon
    to_lat = destination.lat
    to_lon = destination.lon

    # Build transport modes part dynamically
    transport_modes_str = ", ".join([f"{{mode: {mode}}}" for mode in transport_modes])
    if return_points_of is None:
        return_points_of = transport_modes

    query = f"""
        {{
            plan(
                from: {{ lat: {from_lat}, lon: {from_lon} }}
                to: {{ lat: {to_lat}, lon: {to_lon} }}
                date: "{date}"
                time: "{time}"
                transportModes: [{transport_modes_str}]
            ) {{
                itineraries {{
                    start
                    end
                    legs {{
                        mode
                        from {{ name lat lon }}
                        to {{ name lat lon }}
                        legGeometry {{ length points }}
                    }}
                }}
            }}
        }}
    """

    headers = {
        "Content-Type": "application/json",
    }
    url = "http://localhost:9080/otp/gtfs/v1"

    # Send the request
    response = requests.post(url, json={"query": query}, headers=headers)

    # Check status and get JSON
    if response.status_code == 200:
        data = response.json()
        # get shortest itinerary
        itineraries = data["data"]["plan"]["itineraries"]
        if not itineraries:
            return None
        shortest_itinerary = min(
            itineraries,
            key=lambda x: datetime.fromisoformat(x["end"]) - datetime.fromisoformat(x["start"]),
        )
        route = []
        modality_desc = []
        for leg in shortest_itinerary["legs"]:
            if leg["mode"] not in return_points_of:
                continue
            points = polyline.decode(leg["legGeometry"]["points"])
            route.extend(points[:-1])
            modality_desc.extend([f'oepnv-{leg["mode"].lower()}'] * (len(points) - 1))
        # add last point
        route.append((destination.lat, destination.lon))
        modality_desc.append("oepnv-walk")
        return route, modality_desc
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")
