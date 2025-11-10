from typing import List, Union
import folium
from folium.plugins import Draw
import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
from streamlit_folium import st_folium


from schulwege.components.project_components import config_editor, delete_project_dialog
from schulwege.db import (
    compute_segments,
    get_all_projects,
    get_project_by_id,
    get_session,
    update_project_segments,
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


def compute_feature_groups(projects: Union[List[Project], Project], frequency: int):
    if isinstance(projects, Project):
        projects = [projects]
    all_locations = []
    all_segements = []
    for project in projects:
        all_locations.extend(project.locations)
        all_segements.extend(project.segments)

    modalities = sorted(
        set(seg.modality for seg in all_segements),
        key=lambda x: list(MODALITY_MAPPING.keys()).index(x),
    )
    fgs = {
        modality: folium.FeatureGroup(name=MODALITY_MAPPING[modality]) for modality in modalities
    }
    fgs.update({"adressen": folium.FeatureGroup(name="Adressen")})
    fgs_colors = {modality: COLORS[i % len(COLORS)] for i, modality in enumerate(modalities)}
    fgs_colors["adressen"] = "gray"
    for loc in all_locations:
        folium.Marker(
            location=[loc.lat, loc.lon],
            icon=folium.Icon(color=fgs_colors["adressen"], icon="user", prefix="fa"),
        ).add_to(fgs["adressen"])
    dedup_dict = {}
    for seg in all_segements:
        key = (seg.lat_from, seg.lon_from, seg.lat_to, seg.lon_to, seg.modality)
        if key in dedup_dict:
            dedup_dict[key].frequency += seg.frequency
        else:
            dedup_dict[key] = seg
    all_segements = list(dedup_dict.values())
    for seg in all_segements:
        if seg.frequency >= frequency:
            folium.PolyLine(
                [(seg.lat_from, seg.lon_from), (seg.lat_to, seg.lon_to)],
                color=fgs_colors[seg.modality],
                weight=5,
                opacity=0.8,
            ).add_to(fgs[seg.modality])
    return fgs, modalities, fgs_colors


def get_poi_map(projects: Union[List[Project], Project]):
    if isinstance(projects, Project):
        projects = [projects]
    center_location_lat = sum(p.main_location.lat for p in projects) / len(projects)
    center_location_lon = sum(p.main_location.lon for p in projects) / len(projects)
    map = folium.Map(
        location=[center_location_lat, center_location_lon],
        zoom_start=15,
    )
    for project in projects:
        folium.Marker(
            location=[project.main_location.lat, project.main_location.lon],
            icon=folium.Icon(color="red", icon="school", prefix="fa"),
        ).add_to(map)
    return map


def span_legend(fgs_colors, modalities):
    st.markdown(
        "".join(
            [
                f"<span style='background-color: {fgs_colors[modality]}; padding: 5px; margin-right: 5px; color: white; border-radius: 3px;'>{MODALITY_MAPPING[modality]}</span>"
                for modality in modalities
            ]
        ),
        unsafe_allow_html=True,
    )


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
        del st.session_state["current_frequency"]
        del st.session_state["feature_groups"]
        del st.session_state["fgs_colors"]
        del st.session_state["modalities"]
    st.session_state["session"] = id
    if "current_frequency" not in st.session_state:
        st.session_state["current_frequency"] = None
    if "feature_groups" not in st.session_state:
        st.session_state["feature_groups"] = None
    if "fgs_colors" not in st.session_state:
        st.session_state["fgs_colors"] = None
    if "modalities" not in st.session_state:
        st.session_state["modalities"] = None

    session = get_session()
    project = get_project_by_id(session, id)
    if project is None:
        st.error("Projekt nicht gefunden.")
        return

    # add button to navigate back to all projects
    cols = st.columns([1, 2])

    if cols[0].button("← Zurück zu allen Projekten", type="tertiary"):
        router.redirect(*router.build("projects", {"id": "all"}))
    cols[0].markdown(
        f"## {project.main_location.name if project.main_location.name else project.main_location.to_string()}"
    )
    cols[0].info(f"**Erstellt am:** {project.created_at.strftime('%d.%m.%Y %H:%M')}")
    cols[0].info(f"**Anzahl der Adressen von Schüler:innen:** {len(project.locations)}")

    # --- Routes recomputation ---
    expander = cols[0].expander("Schulwege konfigurieren")
    with expander:
        edited_config = config_editor(project, MODALITY_MAPPING)
        if st.button("Schulwege neu berechnen"):
            with st.status("Berechne Schulwege...") as status:
                update_project_segments(
                    session,
                    project,
                    config=edited_config,
                    notif_callback=lambda msg: status.update(label=msg, state="running"),
                )
                st.session_state["feature_groups"] = None
                status.update(label="Berechnung abgeschlossen", state="complete")
            st.rerun()

    # --- Slider for frequency ---
    frequency = cols[0].slider(
        "Hochfrequentierte Schulwege hervorheben",
        min_value=1,
        max_value=len(project.locations),
        value=min(len(project.locations), 5),
        help="Wie viele Schüler:innen müssen denselben Weg gehen, damit er hervorgehoben wird.",
    )

    # --- Update polylines based on slider ---
    if (
        frequency != st.session_state["current_frequency"]
        or st.session_state["feature_groups"] is None
    ):
        st.session_state["current_frequency"] = frequency
        feature_groups, modalities, fgs_colors = compute_feature_groups(project, frequency)
        st.session_state["modalities"] = modalities
        st.session_state["fgs_colors"] = fgs_colors
        st.session_state["feature_groups"] = list(feature_groups.values())

    # --- Display map ---
    with cols[1]:
        map = get_poi_map(project)
        layer_control = folium.LayerControl(collapsed=False)
        Draw(export=True).add_to(map)

        st_folium(
            map,
            feature_group_to_add=st.session_state["feature_groups"],
            layer_control=layer_control,
            key="map",
            width=None,
            height=800,
            returned_objects=[],
        )
        span_legend(st.session_state["fgs_colors"], st.session_state["modalities"])


def combine_projects(router: StreamlitRouter, ids: str):

    # --- session state setup ---
    if "session" in st.session_state and st.session_state["session"] != ids:
        del st.session_state["current_frequency"]
        del st.session_state["feature_groups"]
        del st.session_state["fgs_colors"]
        del st.session_state["modalities"]
    st.session_state["session"] = ids
    if "current_frequency" not in st.session_state:
        st.session_state["current_frequency"] = None
    if "feature_groups" not in st.session_state:
        st.session_state["feature_groups"] = None
    if "fgs_colors" not in st.session_state:
        st.session_state["fgs_colors"] = None
    if "modalities" not in st.session_state:
        st.session_state["modalities"] = None

    session = get_session()

    cols = st.columns([1, 2])
    if cols[0].button("← Zurück zu allen Projekten", type="tertiary"):
        router.redirect(*router.build("projects", {"id": "all"}))
    cols[0].markdown("## Kombinierte Projekte")
    ids = [int(i) for i in ids.split(",") if i.isdigit()]
    projects = [get_project_by_id(session, id) for id in ids]
    projects = [project for project in projects if project is not None]
    if not projects:
        cols[0].warning("Keine gültigen Projekte gefunden.")
        return
    for project in projects:
        cols[0].info(
            f"**{project.main_location.name if project.main_location.name else project.main_location.to_string()}** - Erstellt am {project.created_at.strftime('%d.%m.%Y %H:%M')} - {len(project.locations)} Adressen"
        )

    # --- Slider for frequency ---
    all_locations = []
    for project in projects:
        all_locations.extend(project.locations)
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

        feature_groups, modalities, fgs_colors = compute_feature_groups(projects, frequency)
        st.session_state["modalities"] = modalities
        st.session_state["fgs_colors"] = fgs_colors
        st.session_state["feature_groups"] = list(feature_groups.values())

    # --- Display map ---
    with cols[1]:
        map = get_poi_map(projects)
        layer_control = folium.LayerControl(collapsed=False)
        Draw(export=True).add_to(map)

        st_folium(
            map,
            feature_group_to_add=st.session_state["feature_groups"],
            layer_control=layer_control,
            key="map_combined",
            width=None,
            height=800,
            returned_objects=[],
        )
        span_legend(st.session_state["fgs_colors"], st.session_state["modalities"])


def projects(router: StreamlitRouter, id: Union[str, int]):

    if id == "all":
        projects_list(router)
    else:
        project_detail(router, id)
