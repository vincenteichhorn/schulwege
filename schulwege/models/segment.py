from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String

from schulwege.models.base import Base


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
    project = relationship("Project", back_populates="segments")

    def __repr__(self):
        return f"<Segment from=({self.lat_from}, {self.lon_from}) to=({self.lat_to}, {self.lon_to}) frequency={self.frequency}>"
