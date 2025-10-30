from typing import Dict, List


class Address:
    def __init__(self, data: Dict):
        self.amenity: str = data.get("amenity")
        self.house_number: str = data.get("house_number")
        self.road: str = data.get("road")
        self.quarter: str = data.get("quarter")
        self.suburb: str = data.get("suburb")
        self.city: str = data.get("city")
        self.state: str = data.get("state")
        self.iso3166_2_lvl4: str = data.get("ISO3166-2-lvl4")
        self.postcode: str = data.get("postcode")
        self.country: str = data.get("country")
        self.country_code: str = data.get("country_code")

    def __repr__(self):
        return f"<Address city={self.city} road={self.road}>"

    def to_string(self) -> str:
        parts = []
        if self.house_number:
            parts.append(self.house_number)
        if self.road:
            parts.append(self.road)
        if self.city:
            parts.append(self.city)
        if self.postcode:
            parts.append(self.postcode)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


class Location:
    def __init__(self, data: Dict):
        self.place_id: int = data.get("place_id")
        self.licence: str = data.get("licence")
        self.osm_type: str = data.get("osm_type")
        self.osm_id: int = data.get("osm_id")
        self.lat: float = float(data.get("lat"))
        self.lon: float = float(data.get("lon"))
        self.class_: str = data.get("class")  # 'class' is a reserved keyword
        self.type: str = data.get("type")
        self.place_rank: int = data.get("place_rank")
        self.importance: float = data.get("importance")
        self.addresstype: str = data.get("addresstype")
        self.name: str = data.get("name")
        self.display_name: str = data.get("display_name")
        self.address: Address = Address(data.get("address", {}))
        self.boundingbox: List[float] = [float(coord) for coord in data.get("boundingbox", [])]

    def __repr__(self):
        return f"<Location name={self.name} city={self.address.city} lat={self.lat} lon={self.lon}>"


class Project:
    def __init__(self, name: str, uuid: str):
        self.name = name
        self.uuid = uuid
        self.school_location: Location | None = None

    def __repr__(self):
        return f"<Project name={self.name} uuid={self.uuid}>"
