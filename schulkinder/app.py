from routes import new_project, projects, home
import streamlit as st
from streamlit_router import StreamlitRouter

from components.navbar import navbar
from schulkinder.maps.nominatim import get_nominatim_status

ROUTES = [
    {"endpoint": "/", "view": home, "name": "Startseite"},
    {
        "endpoint": "/projects/<uuid>",
        "view": projects,
        "name": "Projekte",
        "default_args": {"uuid": "all"},
    },
    {"endpoint": "/new", "view": new_project, "name": "Neues Projekt"},
]


if __name__ == "__main__":

    st.set_page_config(page_title="Schulkinder", layout="wide")

    router = StreamlitRouter()
    for route in ROUTES:
        router.register(route["view"], route["endpoint"])
    navbar(ROUTES, router)

    router.serve()
