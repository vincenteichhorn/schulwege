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

    header(
        router,
        "Hochfrequentierte Schulwege",
        subtitle="Die Gesamtkarte der Schulwege aggregiert die Wege aus allen Projekten.",
    )

    st.sidebar.markdown(
        """
        <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 8px;">Aktionen</div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button(
        "Projektübersicht →",
        type="primary",
    ):
        router.redirect(*router.build("overview"))

    if st.sidebar.button("Neues Projekt erstellen →", type="secondary"):
        router.redirect(*router.build("new"))

    session = get_session()

    cols = st.columns([1, 3])

    if "form_progress" not in st.session_state:
        st.session_state.form_progress = 1

    all_projects = get_all_projects(session)
    selected_projects = cols[0].multiselect(
        "(1) Schulen auswählen",
        options=all_projects,
        default=[all_projects[0]] if all_projects else [],
        format_func=lambda project: project.main_location.to_string(),
        key="home_project_filter",
        accept_new_options=False,
        help="Wähle eine oder mehrere Schulen aus, um die Schulwege auf der Karte anzuzeigen. Die Karte zeigt die aggregierten Schulwege für die ausgewählten Schulen an.",
    )
    st.session_state.form_progress = 2 if selected_projects else 1

    maps = {
        "Heatmap Frequenz": segment_heatmap,
        "Modalität": segment_modality_map,
    }
    selected_map = cols[0].selectbox(
        "(2) Kartenansicht auswählen",
        list(maps.keys()),
        disabled=st.session_state.form_progress < 2,
        help="Wähle die gewünschte Kartenansicht aus, um die Schulwege auf der Karte anzuzeigen. Die Heatmap zeigt die Häufigkeit der Schulwege an, während die Modalitätskarte die Art der Fortbewegung (z.B. zu Fuß, Fahrrad, Auto) darstellt.",
    )

    directions = {
        "Hinweg": "to_school",
        "Rückweg": "from_school",
    }
    selected_direction = cols[0].selectbox(
        "(3) Richtung auswählen",
        list(directions.keys()),
        disabled=st.session_state.form_progress < 2,
        help="Wähle die Richtung der Schulwege aus, die auf der Karte angezeigt werden sollen. Der Hinweg zeigt die Wege von den Wohnorten der Schüler:innen zur Schule, während der Rückweg die Wege von der Schule zurück zu den Wohnorten darstellt.",
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
    with cols[0]:
        info_badges(info)
        st.markdown("---")

    if len(segments) > 0:
        tmp_file = export_projects(session, [project.id for project in selected_projects])
        with open(tmp_file, "rb") as f:
            cols[0].download_button(
                label="Geodaten herunterladen",
                data=f,
                file_name="schulwege_projekte.zip",
                mime="application/zip",
                help="Lade die Geodaten der ausgewählten Projekte als ZIP-Datei herunter. Die ZIP-Datei enthält die Geodaten der Schulwege in den Formaten GeoJSON und Shapefile, die in GIS-Software oder Kartenanwendungen verwendet werden können.",
            )

    with cols[1]:

        if len(segments) == 0:
            st.info("Bitte wähle mindestens eine Schule aus, um die Karte anzuzeigen.")
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
