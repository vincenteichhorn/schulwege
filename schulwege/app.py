import streamlit as st
from streamlit_router import StreamlitRouter
from dotenv import load_dotenv

from schulwege.endpoints.database import get_engine, init_db
from schulwege.routes.home import home
from schulwege.routes.overview import overview
from schulwege.routes.project import project
from schulwege.routes.new import new


def main():
    st.set_page_config(page_title="Schulwege", layout="wide", initial_sidebar_state="collapsed")

    router = StreamlitRouter()
    router.register(home, "/")
    router.register(overview, "/overview")
    router.register(project, "/project/<id>")
    router.register(new, "/new")
    router.serve()


if __name__ == "__main__":
    load_dotenv()
    engine = get_engine()
    init_db(engine)
    main()
