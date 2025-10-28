import asyncio
import logging
import os
from pathlib import Path
import docker
from fastapi import FastAPI
import requests
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import osmnx as ox
import pickle

from src.places import PLACES
from src.nominatim import NominatimManager
from src.util.global_state import GlobalState
from src.util.functions import load_json, save_json

PARENT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = Path(__file__).parent.parent / "data"
GLOBAL_STATE_PATH = DATA_DIR / "global_state.json"


async def on_startup():

    logging.basicConfig(level=logging.INFO)

    load_dotenv(dotenv_path=PARENT_DIR / ".env", override=True)

    os.makedirs(DATA_DIR, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.log_console = True
    ox.settings.cache_folder = str(DATA_DIR / "osmnx_cache")

    state = await GlobalState.get_instance()
    await state.load_from_json(GLOBAL_STATE_PATH)

    await state.set("data_dir", str(DATA_DIR))


async def on_shutdown():
    state = await GlobalState.get_instance()
    await state.save_to_json(GLOBAL_STATE_PATH)
    nominatim_manager = NominatimManager.get_instance()
    nominatim_manager.stop_running()


@asynccontextmanager
async def lifespan(api: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


api = FastAPI(lifespan=lifespan)


@api.get("/api")
async def root():
    return {"message": "Schulkinder API is running."}


@api.get("/api/places/")
async def get_places():
    return {"places": list(PLACES.keys())}


@api.get("/api/start/{place}")
async def start_nominatim(place: str):
    if place not in PLACES:
        return {"error": "Place not recognized."}

    region = PLACES[place]

    nominatim_manager = NominatimManager.get_instance()
    status = await nominatim_manager.start_container(region)

    return {"message": f"Nominatim started for {place}.", "status": status}


@api.get("/api/stop/{place}")
async def stop_nominatim(place: str):
    if place not in PLACES:
        return {"error": "Place not recognized."}

    region = PLACES[place]

    nominatim_manager = NominatimManager.get_instance()
    nominatim_manager.stop_container(region)
    return {"message": f"Nominatim stopped for {place}."}


@api.get("/api/status/{place}")
async def nominatim_status(place: str):
    if place not in PLACES:
        return {"error": "Place not recognized."}

    region = PLACES[place]

    nominatim_manager = NominatimManager.get_instance()
    status = nominatim_manager.status(region)

    return {"place": place, "region": region, "status": status}


@api.get("/api/location/{query}")
async def geocode_location(query: str):
    nominatim_manager = NominatimManager.get_instance()
    status = nominatim_manager.status()
    if status.get("nominatim_status", {}).get("error"):
        return {
            "error": "Nominatim is not running. Please start Nominatim before making geocoding requests."
        }
    host_port = nominatim_manager.host_port
    region = (
        nominatim_manager.running_container.lstrip(
            os.getenv("NOMINATIM_BASE_CONTAINER_NAME", "nominatim-")
        )
        if nominatim_manager.running_container
        else "unknown"
    )
    body = requests.get(f"http://localhost:{host_port}/search.php", params={"q": query})
    return {"region": region, "query": query, "results": body.json()}
