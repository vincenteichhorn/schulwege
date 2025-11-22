import streamlit as st
from streamlit_router import StreamlitRouter

from schulwege.endpoints.database import get_engine, init_db
from schulwege.routes.home import home
from schulwege.routes.project import project
from schulwege.routes.new import new


def main():
    st.set_page_config(page_title="Schulwege", layout="wide")
    router = StreamlitRouter()

    router.register(home, "/")
    router.register(project, "/projects/<id>")
    router.register(new, "/new")

    router.serve()


if __name__ == "__main__":
    engine = get_engine()
    init_db(engine)
    main()
