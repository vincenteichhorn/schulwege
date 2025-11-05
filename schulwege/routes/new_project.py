import time
import uuid
import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
import folium
from streamlit_folium import st_folium

from schulwege.maps.nominatim import (
    get_locations_from_addresses,
    get_nominatim_status,
    search_locations,
)
from db import create_project, get_session


def _search_and_update_locations(query: str):
    if query != st.session_state["last_query"] and len(query) > 3:
        st.session_state["last_query"] = query
        st.session_state["search_results"] = search_locations(query)

    option_map = {loc.place_id: loc for loc in st.session_state["search_results"]}
    selected_school = list(option_map.keys())[0] if len(option_map) == 1 else None
    return option_map, selected_school


def new_project(router: StreamlitRouter):

    st.title("Neues Projekt erstellen")

    nominatim_status = get_nominatim_status()
    if not nominatim_status:
        st.error("Nominatim Backend ist nicht erreichbar.")
        return

    if "last_query" not in st.session_state:
        st.session_state["last_query"] = ""
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = []
    if "selected_column" not in st.session_state:
        st.session_state["selected_column"] = None
    if "current_df" not in st.session_state:
        st.session_state["current_df"] = None

    st.markdown("### 1. Schule suchen")
    school_location = None
    query = st.text_input("Namen oder die Adresse der Schule", key="school_query")
    option_map, selected_school = _search_and_update_locations(query)

    if len(option_map) == 0 and len(query) > 3:
        st.warning("Keine Schulen gefunden. Bitte versuchen Sie es mit einer anderen Suche.")

    if len(option_map) > 1 and selected_school is None:
        selected_school = st.pills(
            "Suchergebnisse",
            options=option_map.keys(),
            format_func=lambda pid: f"{option_map[pid].name} ({option_map[pid].to_string()})",
            selection_mode="single",
        )
    if selected_school:
        st.info(
            "Schule ausgewählt: "
            f"{option_map[selected_school].name}, "
            f"{option_map[selected_school].to_string()}"
        )
        school_location = option_map[selected_school]

    if school_location is not None:
        st.markdown("### 2. Adressliste hochladen")

        uploaded_file = st.file_uploader("CSV-Datei mit Adressen hochladen", type=["csv"])

        if uploaded_file is not None:
            st.session_state["current_df"] = pd.read_csv(uploaded_file)
            st.dataframe(st.session_state["current_df"])
            option_map = {col: col for col in st.session_state["current_df"].columns}
            selected_column = st.pills(
                "Spalte mit Adressen auswählen",
                options=option_map.keys(),
                format_func=lambda col: f"{col}",
                selection_mode="single",
            )
            st.session_state["selected_column"] = selected_column

    if (
        school_location is not None
        and st.session_state["selected_column"] is not None
        and st.session_state["current_df"] is not None
    ):
        st.markdown("### 3. Überprüfen und Projekt erstellen")
        df = st.session_state["current_df"]
        create = st.button(f"Projekt erstellen")
        if create:
            df = st.session_state["current_df"]
            with st.status("Adressen werden überprüft...") as s:
                locations, errors = get_locations_from_addresses(
                    df[st.session_state["selected_column"]].tolist(),
                    notif_callback=lambda msg: s.update(label=msg, state="running"),
                )
                s.update(label="Überprüfung abgeschlossen", state="complete")
            if errors:
                st.warning(
                    f"{len(errors)}/{len(df[st.session_state['selected_column']])} Adressen konnten nicht aufgelöst werden und wurden übersprungen."
                )
                error_df = pd.DataFrame(errors, columns=["Ungelöste Adressen"])
                st.dataframe(error_df, hide_index=False)
            if len(locations) == 0:
                st.error("Keine gültigen Adressen zum Erstellen des Projekts.")
            else:
                with st.status("Projekt wird erstellt...") as s:
                    session = get_session()
                    project = create_project(
                        session=session,
                        main_location=school_location,
                        locations=locations,
                        config=[
                            {"modality": "oepnv", "radius": float("nan")},
                            {"modality": "walk", "radius": float("nan")},
                            {"modality": "bike", "radius": float("nan")},
                        ],
                        notif_callback=lambda msg: s.update(label=msg, state="running"),
                    )

                st.session_state["search_results"] = []
                st.session_state["selected_column"] = None
                st.session_state["current_df"] = None
                st.session_state["last_query"] = ""
                router.redirect(*router.build("projects", {"id": str(project.id)}))
