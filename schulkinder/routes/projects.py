import streamlit as st
from streamlit_router import StreamlitRouter


def projects_list(router: StreamlitRouter):
    st.title("Projekte Übersicht")
    st.write("Hier ist eine Liste aller Projekte.")


def project_detail(router: StreamlitRouter, uuid: str):
    st.title(f"Projekt Detail: {uuid}")
    st.write(f"Details für das Projekt mit der UUID: {uuid}")


def projects(router: StreamlitRouter, uuid: str):

    if uuid == "all":
        projects_list(router)
    else:
        project_detail(router, uuid)
