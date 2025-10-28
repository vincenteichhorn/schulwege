import asyncio
import itertools
import json
import os
from pathlib import Path
from pathlib import Path
import osmnx as ox
from pyrosm import OSM

import aiofiles
import requests
from tqdm import tqdm

from src.util.global_state import GlobalState


def load_json(file_path: str, create_if_missing: bool = False) -> dict:
    """
    Load a JSON file and return its contents as a dictionary.
    If the file does not exist, return an empty dictionary.

    Args:
        file_path (str): The path to the JSON file.
        create_if_missing (bool): If True, create an empty file if it does not exist.

    Returns:
        dict: The contents of the JSON file or an empty dictionary if the file does not exist.
    """

    file_path = Path(file_path)
    if not file_path.exists():
        if create_if_missing:
            save_json({}, file_path)
        return {}
    with open(file_path, "r") as f:
        return json.load(f)


def save_json(data: dict, file_path: str) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data (dict): The data to save.
        file_path (str): The path to the JSON file.

    """
    file_path = Path(file_path)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def get_graph_bbox(graph):
    """Get the bounding box of an OSMnx graph."""
    min_lat, min_lon, max_lat, max_lon = None, None, None, None
    for node, data in graph.nodes(data=True):
        y = data["y"]
        x = data["x"]
        if min_lat is None or y < min_lat:
            min_lat = y
        if max_lat is None or y > max_lat:
            max_lat = y
        if min_lon is None or x < min_lon:
            min_lon = x
        if max_lon is None or x > max_lon:
            max_lon = x
    return [min_lat, min_lon, max_lat, max_lon]


async def load_ox_graphml(graph_id):
    """Load an OSMnx graph from a GraphML file given its graph ID."""

    state = await GlobalState.get_instance()
    data_dir = await state.get("data_dir")
    if not os.path.exists(f"{data_dir}/graphs/{graph_id}.graphml"):
        raise FileNotFoundError(f"GraphML file for graph ID {graph_id} not found.")
    graph = ox.load_graphml(f"{data_dir}/graphs/{graph_id}.graphml")
    bbox = get_graph_bbox(graph)
    return graph, bbox


async def download_ox_graphml(place):
    """Save an OSMnx graph to a GraphML file given its graph ID."""

    graph = ox.graph_from_place(place, network_type="all")
    state = await GlobalState.get_instance()
    data_dir = await state.get("data_dir")
    if not os.path.exists(f"{data_dir}/graphs/"):
        os.makedirs(f"{data_dir}/graphs/")
    ox.save_graphml(graph, f"{data_dir}/graphs/{place}.graphml")


async def get_region_url(region):
    """Get the file path for a region file from the global state."""
    region_path = f"https://download.geofabrik.de/{region}-latest.osm.pbf"
    return region_path


def batch_iter(iterable, n=100):
    """Yield successive n-sized chunks from iterable."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, n))
        if not chunk:
            break
        yield chunk
