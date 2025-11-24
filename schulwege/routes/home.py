import pandas as pd
import streamlit as st
from streamlit_router import StreamlitRouter
from schulwege.components.table import TableButton, table
from schulwege.components.header import header
from schulwege.endpoints.database import get_session
from schulwege.models.project import Project


@st.dialog("Projekt löschen")
def confirm_delete_project(project_id: int, session):
    st.write(
        "Sind Sie sicher, dass Sie dieses Projekt löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden."
    )
    if st.button("Löschen", type="primary"):
        session.delete(session.get(Project, project_id))
        session.commit()
        st.success("Projekt erfolgreich gelöscht.")
        st.rerun()


def home(router: StreamlitRouter):

    header(router, "Hochfrequente Schulwege | Projektübersicht")

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
                "Erstellt am": project.created_at.strftime("%d.%m.%Y %H:%M"),
                "Segmente": len(project.segments),
                "Projektseite": TableButton(
                    "Projekt anzeigen",
                    lambda _: router.redirect(*router.build("project", {"id": project.id})),
                    key=f"project_{project.id}_view",
                ),
                "Löschen": TableButton(
                    "Projekt löschen",
                    lambda _: (confirm_delete_project(project.id, session)),
                    key=f"project_{project.id}_delete",
                ),
            }
            for project in projects
        ]
    )
    if not df.empty:
        table(df, widths=[0.5, 3, 3, 2, 1, 2, 2], header=True)
    else:
        st.info(
            "Es sind noch keine Projekte vorhanden. Erstellen Sie ein neues Projekt, um zu beginnen."
        )
