import streamlit as st
from streamlit_router import StreamlitRouter
from streamlit_folium import st_folium

from schulwege.components.header import header
from schulwege.components.info_badges import info_badges
from schulwege.components.maps import (
    export_project,
    segment_heatmap,
    segment_modality_map,
)
from schulwege.endpoints.database import get_session
from schulwege.models.project import Project


def project(router: StreamlitRouter, id: int):

    session = get_session()
    project = session.get(Project, id)

    header(
        router,
        f"{project.get_name()}",
        redirect={
            "route": "home",
            "args": {},
            "desc": "← Zurück zur Startseite",
        },
    )
    info = [
        f"**Standort**: {project.main_location.to_string()}",
        f"Erstellt am {project.created_at.strftime('%d.%m.%Y')}",
    ]
    if len(project.segments) > 0:
        info.append(f"{len(project.segments)} Segmente")

    info_badges(info)

    cols = st.columns([1, 3], gap="large")

    maps = {
        "Heatmap Frequenz": segment_heatmap,
        "Modalität": segment_modality_map,
    }

    with cols[0]:
        selected_map = st.selectbox(
            "Kartenansicht auswählen",
            list(maps.keys()),
        )
        tmp_file = export_project(project)
        with open(tmp_file, "rb") as f:
            st.download_button(
                label="Download Projektdaten",
                data=f,
                file_name=f"projekt_{project.id}.zip",
                mime="application/zip",
            )

    with cols[1]:
        map_function = maps[selected_map]
        map, legend_html = map_function(project.segments)
        st.markdown(
            f"""
            <div style="font-weight: bold; margin-bottom: 8px;">{legend_html}</div>
            """,
            unsafe_allow_html=True,
        )
        st_folium(
            map,
            use_container_width=True,
            height=600,
            returned_objects=[],
        )
