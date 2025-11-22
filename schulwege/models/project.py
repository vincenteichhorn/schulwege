from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, Integer, ForeignKey, String
from typing import List, Optional

from schulwege.models.base import Base
from schulwege.models.location import Location
from schulwege.models.segment import Segment


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    main_location_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )
    main_location: Mapped[Optional[Location]] = relationship(
        "Location", foreign_keys=[main_location_id], post_update=True, uselist=False
    )

    segments: Mapped[List["Segment"]] = relationship(
        "Segment",
        foreign_keys=[Segment.project_id],
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def get_name(self) -> str:
        return self.name or f"Projekt {self.id}"

    def __repr__(self):
        return f"<Project created_at={self.created_at} id={self.id} name={self.name}>"
