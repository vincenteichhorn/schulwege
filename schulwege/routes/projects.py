from typing import List, Union
import folium
from folium.plugins import Draw
import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
from streamlit_folium import st_folium


from schulwege.db import (
    compute_segments,
    delete_project,
    get_all_projects,
    get_project_by_id,
    get_session,
)


from schulwege.models import Project, Segment

COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
    "#393b79",
    "#637939",
    "#8c6d31",
    "#843c39",
]

MODALITY_MAPPING = {
    "walk": "zu Fuß",
    "bike": "Fahrrad",
    "oepnv": "ÖPNV",
    "oepnv-walk": "ÖPNV (zu Fuß)",
    "oepnv-bus": "ÖPNV (Bus)",
    "oepnv-tram": "ÖPNV (Tram)",
    "oepnv-rail": "ÖPNV (Bahn)",
    "oepnv-subway": "ÖPNV (U-Bahn)",
    "oepnv-ferry": "ÖPNV (Fähre)",
    "oepnv-gondola": "ÖPNV (Gondel)",
    "oepnv-funicular": "ÖPNV (Standseilbahn)",
    "adressen": "Adressen",
}


@st.dialog("Projekt löschen")
def delete_project_dialog(project: Project):
    st.warning(
        f"Sind Sie sicher, dass Sie das Projekt für "
        f"{project.main_location.name if project.main_location.name else project.main_location.to_string()} löschen möchten?"
    )
    confirm = st.button("Projekt löschen")
    if confirm:
        session = get_session()
        delete_project(session, project)
        st.success("Projekt gelöscht. Bitte Seite neu laden.")
        st.rerun()


def projects_list(router: StreamlitRouter):
    st.title("Hochfrequentierte Schulwege")

    if not "combine_selected" in st.session_state:
        st.session_state["combine_selected"] = {}

    session = get_session()
    all_projects = get_all_projects(session)

    cols = st.columns(
        [2, 1, 1, 1, 1, 1, 0.5, 0.7],
        gap=None,
    )
    cols[0].markdown("**Schule**")
    cols[1].markdown("**Erstellt am**")
    cols[2].markdown("**Anzahl Adressen**")
    cols[3].markdown("**Anzeigen**")
    cols[4].markdown("**Löschen**")
    cols[5].markdown("**Kombinieren**")
    if cols[6].button("Neu"):
        router.redirect(*router.build("new_project"))
    if cols[7].button(
        "Kombinieren",
        disabled=len(
            [pid for pid, selected in st.session_state["combine_selected"].items() if selected]
        )
        < 2,
        help="Bitte mindestens zwei Projekte zum Kombinieren auswählen.",
    ):
        selected_ids = ",".join(
            str(pid) for pid, selected in st.session_state["combine_selected"].items() if selected
        )
        router.redirect(*router.build("combine_projects", {"ids": selected_ids}))

    combine_selected_copy = st.session_state["combine_selected"].copy()

    for i, project in enumerate(all_projects):
        cols = st.columns([2, 1, 1, 1, 1, 1, 0.5, 0.7], gap=None)

        school_loc = project.main_location
        created_at = project.created_at
        num_locations = len(project.locations)
        cols[0].markdown(f"**{school_loc.name if school_loc.name else school_loc.to_string()}**")
        cols[1].markdown(f"{created_at.strftime('%d.%m.%Y %H:%M')}")
        cols[2].markdown(f"{num_locations} Adressen")
        with cols[3]:
            btn = st.button("Zum Projekt", key=f"project_{project.id}")
            if btn:
                router.redirect(*router.build("projects", {"id": project.id}))
        with cols[4]:
            btn_del = st.button("Löschen", key=f"delete_{project.id}")
            if btn_del:
                delete_project_dialog(project)
        with cols[5]:
            combine_selected_copy[project.id] = st.checkbox(
                " ",
                key=f"combine_{project.id}",
                value=st.session_state["combine_selected"].get(project.id, False),
            )
            if combine_selected_copy[project.id] != st.session_state["combine_selected"].get(
                project.id, False
            ):
                st.session_state["combine_selected"][project.id] = combine_selected_copy[project.id]
                st.rerun()


def project_detail(router: StreamlitRouter, id: Union[str, int]):
    # --- session state setup ---
    if "session" in st.session_state and st.session_state["session"] != id:
        for key in [
            "current_frequency",
        ]:
            if key in st.session_state:
                del st.session_state[key]
    st.session_state["session"] = id
    if "current_frequency" not in st.session_state:
        st.session_state["current_frequency"] = None
    if "feature_groups" not in st.session_state:
        st.session_state["feature_groups"] = None

    session = get_session()
    project = get_project_by_id(session, id)
    if project is None:
        st.error("Projekt nicht gefunden.")
        return

    school_location = project.main_location
    created_at = project.created_at
    locations = project.locations
    segments = project.segments
    config = pd.DataFrame(project.config)

    modalities = sorted(
        set(seg.modality for seg in segments),
        key=lambda x: list(MODALITY_MAPPING.keys()).index(x),
    )
    fgs = {
        modality: folium.FeatureGroup(name=MODALITY_MAPPING[modality]) for modality in modalities
    }
    fgs.update({"adressen": folium.FeatureGroup(name="Adressen")})
    fgs_colors = {modality: COLORS[i % len(COLORS)] for i, modality in enumerate(modalities)}
    fgs_colors["adressen"] = "gray"
    for loc in locations:
        folium.Marker(
            location=[loc.lat, loc.lon],
            icon=folium.Icon(color=fgs_colors["adressen"], icon="user", prefix="fa"),
        ).add_to(fgs["adressen"])

    st.title(f"{school_location.name if school_location.name else school_location.to_string()}")
    cols = st.columns([1, 2])
    cols[0].info(f"**Erstellt am:** {created_at.strftime('%d.%m.%Y %H:%M')}")
    cols[0].info(f"**Anzahl der Adressen von Schüler:innen:** {len(locations)}")

    # --- Routes computation ---
    expander = cols[0].expander("Schulwege konfigurieren")
    with expander:
        config_beatufied = config.copy()
        config_beatufied["modality"] = config_beatufied["modality"].map(MODALITY_MAPPING)
        edited_config = st.data_editor(
            config_beatufied,
            hide_index=True,
            column_config={
                "modality": st.column_config.TextColumn("Verkehrsmittel", disabled=True),
                "radius": st.column_config.NumberColumn(
                    "Radius (m)",
                    min_value=0,
                    help="Radius um den Schulstandort, in dem Adressen berücksichtigt werden (None/Leer = kein Limit).",
                ),
            },
        )
        edited_config["modality"] = edited_config["modality"].map(
            {v: k for k, v in MODALITY_MAPPING.items()}
        )
        if st.button("Schulwege neu berechnen"):
            with st.status("Berechne Schulwege...") as status:
                segments = compute_segments(
                    school_location,
                    locations,
                    config=edited_config.to_dict(orient="records"),
                    notif_callback=lambda msg: status.update(label=msg, state="running"),
                )
                session.query(Segment).filter(Segment.project_id == project.id).delete()
                for segment in segments:
                    segment.project_id = project.id
                    session.add(segment)
                project.config = edited_config.to_dict(orient="records")
                session.commit()
                st.session_state["feature_groups"] = None
                status.update(label="Berechnung abgeschlossen", state="complete")
            st.rerun()

    # --- Slider for frequency ---
    frequency = cols[0].slider(
        "Hochfrequentierte Schulwege hervorheben",
        min_value=1,
        max_value=len(locations),
        value=min(len(locations), 5),
        help="Wie viele Schüler:innen müssen denselben Weg gehen, damit er hervorgehoben wird.",
    )

    # --- Update polylines based on slider ---
    if (
        frequency != st.session_state["current_frequency"]
        or st.session_state["feature_groups"] is None
    ):
        st.session_state["current_frequency"] = frequency

        for seg in segments:
            if seg.frequency >= frequency:
                folium.PolyLine(
                    [(seg.lat_from, seg.lon_from), (seg.lat_to, seg.lon_to)],
                    color=fgs_colors[seg.modality],
                    weight=5,
                    opacity=0.8,
                ).add_to(fgs[seg.modality])
        st.session_state["feature_groups"] = list(fgs.values())

    # --- Display map ---
    with cols[1]:
        map = folium.Map(
            location=[school_location.lat, school_location.lon],
            zoom_start=15,
        )
        folium.Marker(
            location=[school_location.lat, school_location.lon],
            icon=folium.Icon(color="red", icon="school", prefix="fa"),
        ).add_to(map)
        layer_control = folium.LayerControl(collapsed=False)
        Draw(export=True).add_to(map)

        st_folium(
            map,
            feature_group_to_add=st.session_state["feature_groups"],
            layer_control=layer_control,
            key="map",
            width=None,
            height=700,
            returned_objects=[],
        )
        st.markdown(
            "".join(
                [
                    f"<span style='background-color: {fgs_colors[modality]}; padding: 5px; margin-right: 5px; color: white; border-radius: 3px;'>{MODALITY_MAPPING[modality]}</span>"
                    for modality in modalities + ["adressen"]
                ]
            ),
            unsafe_allow_html=True,
        )


def combine_projects(router: StreamlitRouter, ids: str):

    # --- session state setup ---
    if "session" in st.session_state and st.session_state["session"] != ids:
        for key in [
            "current_frequency",
        ]:
            if key in st.session_state:
                del st.session_state[key]
    st.session_state["session"] = ids
    if "current_frequency" not in st.session_state:
        st.session_state["current_frequency"] = None
    if "feature_groups" not in st.session_state:
        st.session_state["feature_groups"] = None

    session = get_session()

    st.title("Kombinierte Projekte")
    ids = [int(i) for i in ids.split(",") if i.isdigit()]
    projects = [get_project_by_id(session, id) for id in ids]
    projects = [project for project in projects if project is not None]
    if not projects:
        st.warning("Keine gültigen Projekte gefunden.")
        return
    cols = st.columns([1, 2])

    for project in projects:
        with cols[0]:
            st.info(
                f"**Schule:** {project.main_location.name if project.main_location.name else project.main_location.to_string()}\n\n"
                f"**Erstellt am:** {project.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"**Anzahl Adressen:** {len(project.locations)}"
            )

    all_segments = []
    all_locations = []
    for project in projects:
        all_segments.extend(project.segments)
        all_locations.extend(project.locations)

    modalities = sorted(
        set(seg.modality for seg in all_segments),
        key=lambda x: list(MODALITY_MAPPING.keys()).index(x),
    )
    fgs = {mod: folium.FeatureGroup(name=MODALITY_MAPPING[mod]) for mod in modalities}
    fgs.update({"adressen": folium.FeatureGroup(name="Adressen")})
    fgs_colors = {mod: COLORS[i % len(COLORS)] for i, mod in enumerate(modalities)}
    fgs_colors["adressen"] = "gray"

    for loc in all_locations:
        folium.Marker(
            location=[loc.lat, loc.lon],
            icon=folium.Icon(color=fgs_colors["adressen"], icon="user", prefix="fa"),
        ).add_to(fgs["adressen"])

    frequency = cols[0].slider(
        "Hochfrequentierte Schulwege hervorheben",
        min_value=1,
        max_value=len(all_locations),
        value=min(len(all_locations), 5),
        help="Wie viele Schüler:innen müssen denselben Weg gehen, damit er hervorgehoben wird.",
    )

    # --- Update polylines based on slider ---
    if (
        frequency != st.session_state["current_frequency"]
        or st.session_state["feature_groups"] is None
    ):
        st.session_state["current_frequency"] = frequency

        for seg in all_segments:
            if seg.frequency >= frequency:
                folium.PolyLine(
                    [(seg.lat_from, seg.lon_from), (seg.lat_to, seg.lon_to)],
                    color=fgs_colors[seg.modality],
                    weight=5,
                    opacity=0.8,
                ).add_to(fgs[seg.modality])
        st.session_state["feature_groups"] = list(fgs.values())

    # --- Display map ---
    with cols[1]:
        map = folium.Map(
            location=[projects[0].main_location.lat, projects[0].main_location.lon],
            zoom_start=13,
        )
        layer_control = folium.LayerControl(collapsed=False)
        Draw(export=True).add_to(map)

        for project in projects:
            folium.Marker(
                location=[project.main_location.lat, project.main_location.lon],
                icon=folium.Icon(color="red", icon="school", prefix="fa"),
            ).add_to(map)

        st_folium(
            map,
            feature_group_to_add=st.session_state["feature_groups"],
            layer_control=layer_control,
            key="map_combined",
            width=None,
            height=700,
            returned_objects=[],
        )
        st.markdown(
            "".join(
                [
                    f"<span style='background-color: {fgs_colors[modality]}; padding: 5px; margin-right: 5px; color: white; border-radius: 3px;'>{MODALITY_MAPPING[modality]}</span>"
                    for modality in modalities
                ]
            ),
            unsafe_allow_html=True,
        )


def projects(router: StreamlitRouter, id: Union[str, int]):

    if id == "all":
        projects_list(router)
    else:
        project_detail(router, id)
