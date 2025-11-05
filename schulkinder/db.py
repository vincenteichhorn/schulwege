from collections import Counter
import math
import os
from typing import Dict, List
from requests import session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from streamlit import cache_resource
from schulkinder.maps.routing import compute_routes, filter_radius_locations
from schulkinder.models import Base, Location, Project, Segment


def get_engine():

    @cache_resource
    def _create_engine():
        db_url = os.getenv("SQL_DATABASE_URL", "sqlite:///data/schulkinder.db")
        engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        return engine

    return _create_engine()


def get_session():
    engine = get_engine()
    SessionLocal = scoped_session(sessionmaker(bind=engine))
    return SessionLocal()


def init_db(engine):
    Base.metadata.create_all(engine)


def get_segments_of_routes(routes: List[List[tuple]], modality: list[list[str]]) -> List[Segment]:
    counter = Counter()
    for route, mods in zip(routes, modality):
        a = route[0]
        for b, mod in zip(route[1:], mods[1:]):
            counter[(a, b, mod)] += 1
            a = b
    segments = [
        Segment(
            lat_from=a[0],
            lon_from=a[1],
            lat_to=b[0],
            lon_to=b[1],
            modality=mod,
            frequency=count,
        )
        for (a, b, mod), count in counter.items()
    ]
    return segments


def compute_segments(
    main_location: Location,
    locations: List[Location],
    config: List[Dict],
    notif_callback=lambda x: None,
) -> List[Segment]:
    all_segments = []
    for cgf in config:
        modality = cgf.get("modality")
        radius = cgf.get("radius")
        filtered_locations = locations
        if not math.isnan(radius):
            filtered_locations = filter_radius_locations(
                main_location, locations, radius_meters=radius
            )
        routes, modality_desc = compute_routes(
            main_location, filtered_locations, network=modality, notif_callback=notif_callback
        )
        segments = get_segments_of_routes(routes, modality=modality_desc)
        all_segments.extend(segments)
    return all_segments


def create_project(
    session,
    main_location: Location,
    locations: List[Location],
    config: List[Dict],
    notif_callback: lambda x: None,
) -> Project:
    all_segments = compute_segments(
        main_location, locations, config=config, notif_callback=notif_callback
    )
    project = Project()
    project.locations = locations
    project.segments = all_segments
    project.config = config

    session.add(project)
    session.flush()

    project.main_location = main_location
    session.commit()
    return project


def get_project_by_id(session, project_id: int) -> Project:
    project = session.query(Project).filter(Project.id == project_id).first()
    return project


def get_all_projects(session) -> List[Project]:
    projects = session.query(Project).all()
    return projects


def update_project_config(session, project: Project, config: List[Dict]):
    project.config = config.copy()
    print(project.config)
    session.commit()


def delete_project(session, project: Project):
    session.delete(project)
    session.commit()
