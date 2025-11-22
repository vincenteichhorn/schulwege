from schulwege.models.base import Base
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Tuple


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    lat: Mapped[float] = mapped_column()
    lon: Mapped[float] = mapped_column()
    osm_id: Mapped[int] = mapped_column()
    display_name: Mapped[Optional[str]] = mapped_column()
    city: Mapped[Optional[str]] = mapped_column()
    road: Mapped[Optional[str]] = mapped_column()
    postcode: Mapped[Optional[str]] = mapped_column()
    country: Mapped[Optional[str]] = mapped_column()
    place_id: Mapped[Optional[int]] = mapped_column()
    osm_type: Mapped[Optional[str]] = mapped_column()
    licence: Mapped[Optional[str]] = mapped_column()
    amenity: Mapped[Optional[str]] = mapped_column()
    house_number: Mapped[Optional[str]] = mapped_column()
    quarter: Mapped[Optional[str]] = mapped_column()
    suburb: Mapped[Optional[str]] = mapped_column()
    state: Mapped[Optional[str]] = mapped_column()
    iso3166_2_lvl4: Mapped[Optional[str]] = mapped_column()
    place_rank: Mapped[Optional[int]] = mapped_column()
    importance: Mapped[Optional[float]] = mapped_column()
    addresstype: Mapped[Optional[str]] = mapped_column()
    boundingbox: Mapped[Optional[str]] = mapped_column()

    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))

    def __repr__(self):
        return f"<Location name={self.name} city={self.city} lat={self.lat} lon={self.lon}>"

    def to_string(self) -> str:
        parts = [
            p for p in [self.road, self.house_number, self.city, self.postcode, self.country] if p
        ]
        return f"{self.name} ({', '.join(parts)})"

    @property
    def coordinates(self) -> Optional[Tuple[float, float]]:
        if self.lat is not None and self.lon is not None:
            return (self.lat, self.lon)
        return None


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
