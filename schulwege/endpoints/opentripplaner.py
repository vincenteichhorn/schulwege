from datetime import datetime
import os
import polyline
import requests
from schulwege.models.location import Location


def get_open_trip_planner_url() -> str:
    """Get the OpenTripPlanner API URL from environment variables."""
    OTP_HOST = "localhost"
    OTP_PORT = os.getenv("OTP_HOST_PORT", "9080")
    return f"http://{OTP_HOST}:{OTP_PORT}/otp/gtfs/v1"


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
    url = get_open_trip_planner_url()

    response = requests.post(url, json={"query": query}, headers=headers)

    if response.status_code == 200:
        data = response.json()

        itineraries = data["data"]["plan"]["itineraries"]
        if not itineraries:
            return [], []
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
