import sys
from schulwege.routes.new_project import new_project
from schulwege.routes.projects import combine_projects, projects
import streamlit as st
from streamlit_router import StreamlitRouter
import streamlit.web.cli as stcli

from schulwege.components.navbar import navbar
from schulwege.db import init_db, get_engine
from schulwege.maps.routing import init_osmnx

ROUTES = [
    {
        "endpoint": "/",
        "view": lambda router: router.redirect(*router.build("projects", {"id": "all"})),
        "name": "Home",
        "show": True,
    },
    {
        "endpoint": "/projects/<id>",
        "view": projects,
        "name": "Projekte",
        "default_args": {"id": "all"},
        "show": True,
    },
    {
        "endpoint": "/combine/<ids>",
        "view": combine_projects,
        "name": "Projekte kombinieren",
        "show": False,
    },
    {"endpoint": "/new", "view": new_project, "name": "Neues Projekt", "show": False},
]


if __name__ == "__main__":

    engine = get_engine()
    init_db(engine)

    init_osmnx()

    st.set_page_config(page_title="Schulkinder", layout="wide")

    router = StreamlitRouter()
    for route in ROUTES:
        router.register(route["view"], route["endpoint"])
    # navbar(ROUTES, router)

    router.serve()
