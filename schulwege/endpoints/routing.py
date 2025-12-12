from collections import Counter
from datetime import datetime, timedelta
import json
from math import atan2, cos, radians, sin, sqrt
import os
from typing import List, Tuple
import osmnx as ox
import networkx as nx
from shapely import MultiPoint
import streamlit as st

from schulwege.endpoints.opentripplaner import get_public_transport_route
from schulwege.models.location import Location
from schulwege.models.project import Project
from schulwege.models.segment import Segment


@st.cache_data(
    persist="disk",
    hash_funcs={Location: lambda loc: (loc.lat, loc.lon) if loc.coordinates else loc.to_string()},
    show_spinner=False,
)
def get_graph_in_hull(
    locations: List[Location], buffer_meters=2000, network_type="all"
) -> nx.MultiDiGraph:
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


def load_model_config() -> List[dict]:
    config_file = os.getenv("MODEL_CONFIG_FILE", "./model_config.json")
    with open(config_file, "r") as f:
        config = json.load(f)
    return config


def get_road_network(locations, network_type: str) -> nx.MultiDiGraph:
    graph = get_graph_in_hull(locations, network_type=network_type)
    return graph


def haversine(locationA: Location, locationB: Location) -> float:
    lat1, lon1 = locationA.lat, locationA.lon
    lat2, lon2 = locationB.lat, locationB.lon
    R = 6371000  # Radius of the Earth in meters
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


def compute_walking_routes(
    main_location: Location,
    locations: List[Location],
    min_radius: float,
    max_radius: float,
    progress_callback=None,
) -> Tuple[List[List[Tuple[float, float]]], List[bool]]:

    if progress_callback:
        progress_callback("Lade Straßennetz für Laufwege...")
    network = get_road_network(locations, network_type="walk")
    routes = []
    directions = []
    origin_node = ox.distance.nearest_nodes(network, main_location.lon, main_location.lat)

    for i, loc in enumerate(locations):
        dist = haversine(main_location, loc)
        if dist < min_radius or dist > max_radius:
            continue
        if progress_callback:
            progress_callback(f"Berechne Laufwege {i+1}/{len(locations)}")
        destination_node = ox.distance.nearest_nodes(network, loc.lon, loc.lat)
        route = ox.shortest_path(network, origin_node, destination_node, weight="length")
        route_coords = [(network.nodes[node]["y"], network.nodes[node]["x"]) for node in route]
        routes.append(route_coords)
        directions.append(True)
        route = ox.shortest_path(network, destination_node, origin_node, weight="length")
        route_coords = [(network.nodes[node]["y"], network.nodes[node]["x"]) for node in route]
        routes.append(route_coords)
        directions.append(False)

    return routes, directions


def compute_bicycling_route(
    main_location: Location,
    locations: List[Location],
    min_radius: float,
    max_radius: float,
    progress_callback=None,
) -> Tuple[List[List[Tuple[float, float]]], List[bool]]:

    if progress_callback:
        progress_callback("Lade Straßennetz für Fahrradwege...")
    network = get_road_network(locations, network_type="bike")
    routes = []
    directions = []
    origin_node = ox.distance.nearest_nodes(network, main_location.lon, main_location.lat)
    for i, loc in enumerate(locations):
        dist = haversine(main_location, loc)
        if dist < min_radius or dist > max_radius:
            continue
        if progress_callback:
            progress_callback(f"Berechne Fahrradwege {i+1}/{len(locations)}")
        destination_node = ox.distance.nearest_nodes(network, loc.lon, loc.lat)
        route = ox.shortest_path(network, origin_node, destination_node, weight="length")
        route_coords = [(network.nodes[node]["y"], network.nodes[node]["x"]) for node in route]
        routes.append(route_coords)
        directions.append(True)
        route = ox.shortest_path(network, destination_node, origin_node, weight="length")
        route_coords = [(network.nodes[node]["y"], network.nodes[node]["x"]) for node in route]
        routes.append(route_coords)
        directions.append(False)
    return routes, directions


def compute_public_transport_walking_route(
    main_location: Location,
    locations: List[Location],
    date: str,
    to_school_time: str,
    from_school_time: str,
    min_radius: float,
    max_radius: float,
    progress_callback=None,
) -> Tuple[List[List[Tuple[float, float]]], List[bool]]:

    def extract_walking_routes(
        route: List[Tuple[float, float]], modalities: List[str]
    ) -> List[List[Tuple[float, float]]]:
        routes = []
        current_start = None
        for j in range(len(route)):
            point = route[j]
            modality = modalities[j]
            if modality == "oepnv-walk":
                if current_start is None:
                    current_start = point
            else:  # if we are nto on walking segment, compute the pending walking route
                if current_start is not None:
                    walking_route = ox.shortest_path(
                        network,
                        ox.distance.nearest_nodes(network, current_start[1], current_start[0]),
                        ox.distance.nearest_nodes(network, point[1], point[0]),
                        weight="length",
                    )
                    walking_route_coords = [
                        (network.nodes[node]["y"], network.nodes[node]["x"])
                        for node in walking_route
                    ]
                    routes.append(walking_route_coords)
                    current_start = None
        return routes

    network = get_road_network(locations, network_type="walk")
    routes = []
    directions = []
    for i, loc in enumerate(locations):
        dist = haversine(main_location, loc)
        if dist < min_radius or dist > max_radius:
            continue
        if progress_callback:
            progress_callback(f"Berechne ÖPNV-Wege {i+1}/{len(locations)}")
        route, modalities = get_public_transport_route(
            origin=main_location,
            destination=loc,
            date=date,
            time=to_school_time,
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
        if len(route) != 0:
            walking_routes = extract_walking_routes(route, modalities)
            routes.extend(walking_routes)
            directions.extend([True] * len(walking_routes))

        route, modalities = get_public_transport_route(
            origin=loc,
            destination=main_location,
            date=date,
            time=from_school_time,
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
        if len(route) != 0:
            walking_routes = extract_walking_routes(route, modalities)
            routes.extend(walking_routes)
            directions.extend([False] * len(walking_routes))

    return routes, directions


def compute_school_routes(
    main_location: Location, locations: List[Location], progress_callback=None
) -> Tuple[List[List[Tuple[float, float]]], List[str]]:

    model_config = load_model_config()
    if not "routing" in model_config:
        raise ValueError("No routing configuration found in model config.")
    routing_config = model_config.get("routing", [])
    routes = []
    route_modalities = []
    directions = []
    for i, route_cfg in enumerate(routing_config):
        modality = route_cfg.get("modality")
        modality_display_name = route_cfg.get("modality_display_name", modality)
        min_radius = route_cfg.get("min_radius", 0)
        max_radius = route_cfg.get("max_radius", -1)

        if max_radius == -1:
            max_radius = float("inf")

        if modality == "walk":
            walking_routes, walking_directions = compute_walking_routes(
                main_location,
                locations,
                min_radius,
                max_radius,
                progress_callback=lambda p: (
                    progress_callback(f"[{i+1}/{len(routing_config)}] {p}")
                    if progress_callback
                    else None
                ),
            )
            routes.extend(walking_routes)
            route_modalities.extend([modality_display_name] * len(walking_routes))
            directions.extend(walking_directions)
        elif modality == "bicycle":
            bike_routes, bike_directions = compute_bicycling_route(
                main_location,
                locations,
                min_radius,
                max_radius,
                progress_callback=lambda p: (
                    progress_callback(f"[{i+1}/{len(routing_config)}] {p}")
                    if progress_callback
                    else None
                ),
            )
            routes.extend(bike_routes)
            route_modalities.extend([modality_display_name] * len(bike_routes))
            directions.extend(bike_directions)
        elif modality == "public_transport_walking":
            now = datetime.now()
            monday = now - timedelta(days=now.weekday())
            now = monday.replace(hour=7, minute=0, second=0, microsecond=0)
            date_str = monday.strftime("%Y-%m-%d")
            to_school_time_str = monday.strftime("%H:%M")
            from_school_time_str = (monday + timedelta(hours=8)).strftime("%H:%M")

            public_transport_walking_routes, public_transport_walking_directions = (
                compute_public_transport_walking_route(
                    main_location,
                    locations,
                    date_str,
                    to_school_time_str,
                    from_school_time_str,
                    min_radius,
                    max_radius,
                    progress_callback=lambda p: (
                        progress_callback(f"[{i+1}/{len(routing_config)}] {p}")
                        if progress_callback
                        else None
                    ),
                )
            )
            routes.extend(public_transport_walking_routes)
            route_modalities.extend([modality_display_name] * len(public_transport_walking_routes))
            directions.extend(public_transport_walking_directions)
        else:
            st.warning(f"Unbekannte Routing-Modality: {modality}")
    return routes, route_modalities, directions


def round_route_coordinates(
    route: List[Tuple[float, float]], precision: int = 5
) -> List[Tuple[float, float]]:
    return [(round(lat, precision), round(lon, precision)) for lat, lon in route]


def merge_segments(segments: List[Segment]) -> List[Segment]:
    segment_dict = {}
    for segment in segments:
        key = (
            segment.lat_from,
            segment.lon_from,
            segment.lat_to,
            segment.lon_to,
            segment.modality,
            segment.direction,
        )
        if key in segment_dict:
            segment_dict[key].frequency += segment.frequency
        else:
            segment_dict[key] = Segment(
                lat_from=segment.lat_from,
                lon_from=segment.lon_from,
                lat_to=segment.lat_to,
                lon_to=segment.lon_to,
                modality=segment.modality,
                frequency=segment.frequency,
                direction=segment.direction,
                is_start=segment.is_start,
            )
    return list(segment_dict.values())


def compute_segments(main_location: Location, locations: List[Location], progress_callback=None):

    location_coords = [(loc.lat, loc.lon) for loc in locations if loc.coordinates is not None]
    rounded_location_coords = set(round_route_coordinates(location_coords))

    routes, route_modalities, directions = compute_school_routes(
        main_location,
        locations,
        progress_callback=progress_callback,
    )

    model_config = load_model_config()
    min_frequency = model_config.get("min_segment_frequency", 0)
    counter = Counter()
    if progress_callback:
        progress_callback("Berechne Routensegmente...")
    for i, (route, modality, direction) in enumerate(zip(routes, route_modalities, directions)):
        if progress_callback:
            progress_callback(f"Berechne Routensegmente {i+1}/{len(routes)}...")
        if len(route) == 0:
            continue
        rounded_route = tuple(round_route_coordinates(route))
        start = rounded_route[0]
        for end in rounded_route[1:]:
            segment_key = (start, end, modality, direction)
            counter[segment_key] += 1
            start = end
    segments = [
        Segment(
            lat_from=start[0],
            lon_from=start[1],
            lat_to=end[0],
            lon_to=end[1],
            modality=modality,
            frequency=count,
            direction="to_school" if direction else "from_school",
            is_start=(start in rounded_location_coords),
        )
        for (start, end, modality, direction), count in counter.items()
        if count >= min_frequency
    ]
    return segments
