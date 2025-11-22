import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
from schulwege.components.table import TableButton, table
from schulwege.components.header import header
from schulwege.endpoints.database import get_session
from schulwege.models.project import Project


def home(router: StreamlitRouter):

    col1, col2 = st.columns([6.85, 1], vertical_alignment="center")

    with col1:
        header(router, "Hochfrequente Schulwege | Projektübersicht")

    with col2:
        if st.button("Neues Projekt erstellen →", type="primary"):
            router.redirect(*router.build("new"))
    session = get_session()
    projects = session.query(Project).order_by(Project.created_at.desc()).all()

    df = pd.DataFrame(
        [
            {
                "ID": project.id,
                "Name": project.get_name(),
                "Standort": project.main_location.to_string() if project.main_location else "N/A",
                "Erstellt am": project.created_at.strftime("%d.%m.%Y"),
                "Segmente": len(project.segments),
                "Link": TableButton(
                    "Projekt anzeigen",
                    lambda _: router.redirect(*router.build("project", {"id": project.id})),
                    key=f"project_{project.id}_view",
                ),
                "Löschen": TableButton(
                    "Projekt löschen",
                    lambda _: (
                        session.delete(session.get(Project, project.id)),
                        session.commit(),
                        st.rerun(),
                    ),
                    key=f"project_{project.id}_delete",
                ),
            }
            for project in projects
        ]
    )
    if not df.empty:
        table(df)
    else:
        st.info(
            "Es sind noch keine Projekte vorhanden. Erstellen Sie ein neues Projekt, um zu beginnen."
        )
