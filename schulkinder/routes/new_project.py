import time
import uuid
import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
import folium
from streamlit_folium import st_folium

from maps.nominatim import get_nominatim_status, search_locations
from models import Location

DEBOUNCE_TIME_MS = 500


def _search_and_update_locations(query: str):
    if query != st.session_state["last_query"] and len(query) > 3:
        st.session_state["last_query"] = query
        time.sleep(DEBOUNCE_TIME_MS / 1000)  # Debounce

        st.session_state["search_results"] = search_locations(query)

    option_map = {loc.place_id: loc for loc in st.session_state["search_results"]}
    selected_school = list(option_map.keys())[0] if len(option_map) == 1 else None
    return option_map, selected_school


def _centered_map(location: Location):
    m = folium.Map(location=[location.lat, location.lon], zoom_start=15)
    folium.Marker(
        location=[location.lat, location.lon],
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)
    return m


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
            format_func=lambda pid: f"{option_map[pid].name} ({option_map[pid].address.to_string()})",
            selection_mode="single",
        )
    if selected_school:
        st.info(
            "Schule ausgewählt: "
            f"{option_map[selected_school].name}, "
            f"{option_map[selected_school].address.to_string()}"
        )
        school_location = option_map[selected_school]

    test_locations = []
    if school_location is not None:
        st.markdown("### 2. Adressliste hochladen")

        uploaded_file = st.file_uploader("CSV-Datei mit Adressen hochladen", type=["csv"])

        if uploaded_file is not None:
            st.session_state["current_df"] = pd.read_csv(uploaded_file)
            st.dataframe(st.session_state["current_df"].head())
            option_map = {col: col for col in st.session_state["current_df"].columns}
            selected_column = st.pills(
                "Spalte mit Adressen auswählen",
                options=option_map.keys(),
                format_func=lambda col: f"{col}",
                selection_mode="single",
            )
            st.session_state["selected_column"] = selected_column

        test_locations = []
        if (
            st.session_state["selected_column"] is not None
            and st.session_state["current_df"] is not None
        ):
            df = st.session_state["current_df"]
            for idx, row in df.iterrows():
                address = row[st.session_state["selected_column"]]
                locs = search_locations(address)
                if locs:
                    test_locations.append(locs[0])
                else:
                    st.warning(f"Keine Ergebnisse für Adresse: {address}. Fehlerhaft?")

    if school_location is not None and len(test_locations) > 0:
        st.markdown("### 3. Überprüfen und bestätigen")
        st.markdown(
            "Die ersten 10 Adressen aus der hochgeladenen Datei sollten hier angezeigt werden."
        )
        map = _centered_map(school_location)
        bbox = map.get_bounds()
        for loc in test_locations[:10]:
            if not (bbox[0][0] <= loc.lat <= bbox[1][0]) or not (
                bbox[0][1] <= loc.lon <= bbox[1][1]
            ):
                bbox[0][0] = min(bbox[0][0], loc.lat)
                bbox[0][1] = min(bbox[0][1], loc.lon)
                bbox[1][0] = max(bbox[1][0], loc.lat)
                bbox[1][1] = max(bbox[1][1], loc.lon)
            folium.Marker(
                location=[loc.lat, loc.lon],
                popup=loc.display_name,
                icon=folium.Icon(color="blue", icon="ok-sign"),
            ).add_to(map)
        map.fit_bounds(bbox)
        st_folium(map, width=None, height=700)

    create = st.button("Projekt erstellen")
    if create:
        st.success("Projekt erfolgreich erstellt!")
        project = {"name": "Neues Projekt", "uuid": uuid.uuid4()}
        st.session_state["search_results"] = []
        st.session_state["selected_column"] = None
        st.session_state["current_df"] = None
        router.redirect(*router.build("projects", {"uuid": project["uuid"]}))
        st.session_state["last_query"] = ""
