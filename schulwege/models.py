from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]]
    lat: Mapped[Optional[float]]
    lon: Mapped[Optional[float]]
    display_name: Mapped[Optional[str]]
    city: Mapped[Optional[str]]
    road: Mapped[Optional[str]]
    postcode: Mapped[Optional[str]]
    country: Mapped[Optional[str]]
    place_id: Mapped[Optional[int]]
    osm_id: Mapped[Optional[int]]
    osm_type: Mapped[Optional[str]]
    licence: Mapped[Optional[str]]
    amenity: Mapped[Optional[str]]
    house_number: Mapped[Optional[str]]
    quarter: Mapped[Optional[str]]
    suburb: Mapped[Optional[str]]
    state: Mapped[Optional[str]]
    iso3166_2_lvl4: Mapped[Optional[str]]
    place_rank: Mapped[Optional[int]]
    importance: Mapped[Optional[float]]
    addresstype: Mapped[Optional[str]]
    boundingbox: Mapped[Optional[str]]

    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="locations",
        foreign_keys=[project_id],
    )

    def __repr__(self):
        return f"<Location name={self.name} city={self.city} lat={self.lat} lon={self.lon}>"

    def to_string(self) -> str:
        parts = [
            p for p in [self.road, self.house_number, self.city, self.postcode, self.country] if p
        ]
        return ", ".join(parts)

    @property
    def coordinates(self) -> Optional[tuple[float, float]]:
        if self.lat is not None and self.lon is not None:
            return (self.lat, self.lon)
        return None


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lat_from: Mapped[float]
    lon_from: Mapped[float]
    lat_to: Mapped[float]
    lon_to: Mapped[float]
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    modality: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(ForeignKey("projects.id"))
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="segments",
        foreign_keys=[project_id],
    )

    def __repr__(self):
        return f"<Segment from=({self.lat_from}, {self.lon_from}) to=({self.lat_to}, {self.lon_to}) frequency={self.frequency}>"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    main_location_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )
    main_location: Mapped[Optional[Location]] = relationship(
        "Location", foreign_keys=[main_location_id], post_update=True, uselist=False
    )

    locations: Mapped[List[Location]] = relationship(
        "Location",
        back_populates="project",
        foreign_keys=[Location.project_id],
        cascade="all, delete-orphan",
    )

    segments: Mapped[List["Segment"]] = relationship(
        "Segment",
        back_populates="project",
        foreign_keys=[Segment.project_id],
        cascade="all, delete-orphan",
    )

    config: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True, default=[])

    def __repr__(self):
        return f"<Project create_at={self.create_at} id={self.id}>"

    @property
    def name(self) -> str:
        if self.main_location:
            return f"Projekt für {self.main_location.to_string()}"
        return "Unbenanntes Projekt"
