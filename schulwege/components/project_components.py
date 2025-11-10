from typing import Dict
import pandas as pd
import streamlit as st

from schulwege.db import get_session
from schulwege.models import Project


def config_editor(project: Project, modality_mapping: Dict[str, str]) -> Dict:
    config = project.config
    config_beatufied = pd.DataFrame(config)
    config_beatufied["modality"] = config_beatufied["modality"].map(modality_mapping)
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
        {v: k for k, v in modality_mapping.items()}
    )
    return edited_config.to_dict(orient="records")


@st.dialog("Projekt löschen")
def delete_project_dialog(project: Project):
    st.warning(
        f"Sind Sie sicher, dass Sie das Projekt für "
        f"{project.main_location.name if project.main_location.name else project.main_location.to_string()} löschen möchten?"
    )
    confirm = st.button("Projekt löschen")
    if confirm:
        session = get_session()
        session.delete(project)
        session.commit()
        st.success("Projekt gelöscht. Bitte Seite neu laden.")
        st.rerun()
