from typing import List
import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
from schulwege.components.info_badges import info_badges
from schulwege.components.maps import export_projects, segment_heatmap, segment_modality_map
from schulwege.components.table import TableButton, table
from schulwege.components.header import header
from schulwege.endpoints.database import get_session
from schulwege.endpoints.routing import merge_segments
from schulwege.models.project import Project
from schulwege.models.location import Location
from schulwege.components.search_box import search_box
from schulwege.models.segment import Segment
from streamlit_folium import st_folium


def search_schools(query: str):
    session = get_session()
    locations = (
        session.query(Project)
        .filter(
            Project.main_location.has(
                Project.main_location.property.mapper.class_.name.ilike(f"%{query}%")
            )
        )
        .all()
    )
    return [project.main_location for project in locations]


def get_all_projects(session) -> List[Project]:
    projects = session.query(Project).order_by(Project.created_at.desc()).all()
    return projects


def get_segments(session, projects: List[Project], direction: str) -> List:
    pids = [project.id for project in projects]
    segments = (
        session.query(Segment)
        .filter(Segment.project_id.in_(pids))
        .filter(Segment.direction == direction)
        .all()
    )
    return merge_segments(segments)


def home(router: StreamlitRouter):

    header(router, "Hochfrequentierte Schulwege")

    if st.sidebar.button("Neues Projekt erstellen →", type="primary"):
        router.redirect(*router.build("new"))

    if st.sidebar.button("Übersicht →", type="primary"):
        router.redirect(*router.build("overview"))

    session = get_session()

    cols = st.columns([1, 3])

    selected_projects = cols[0].multiselect(
        "(1) Schulen auswählen",
        options=get_all_projects(session),
        format_func=lambda project: project.main_location.to_string(),
        key="home_project_filter",
        accept_new_options=False,
    )

    maps = {
        "Heatmap Frequenz": segment_heatmap,
        "Modalität": segment_modality_map,
    }
    selected_map = cols[0].selectbox(
        "Kartenansicht auswählen",
        list(maps.keys()),
    )

    directions = {
        "Hinweg": "to_school",
        "Rückweg": "from_school",
    }
    selected_direction = cols[0].selectbox(
        "Richtung auswählen",
        list(directions.keys()),
    )

    segments = (
        get_segments(session, selected_projects, directions[selected_direction])
        if selected_projects
        else []
    )
    info = [
        f"{len(selected_projects)} Schulen ausgewählt",
        f"{len(segments)} Segmente insgesamt",
    ]

    if len(segments) > 0:
        tmp_file = export_projects(session, [project.id for project in selected_projects])
        with open(tmp_file, "rb") as f:
            cols[0].download_button(
                label="Geodaten herunterladen",
                data=f,
                file_name="schulwege_projekte.zip",
                mime="application/zip",
            )

    with cols[1]:
        info_badges(info)

        if len(segments) == 0:
            st.info("Bitte wählen Sie mindestens eine Schule aus, um die Karte anzuzeigen.")
            return

        map_function = maps[selected_map]
        map, legend_html = map_function(segments)
        st.markdown(
            f"""
            <div style="font-weight: bold; margin-bottom: 8px;">{legend_html}</div>
            """,
            unsafe_allow_html=True,
        )
        st_folium(
            map,
            use_container_width=True,
            height=900,
            returned_objects=[],
        )
