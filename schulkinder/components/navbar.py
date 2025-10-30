from typing import Dict, List
from streamlit_router import StreamlitRouter
import streamlit as st


def navbar(routes: List[Dict], router: StreamlitRouter):

    with st.sidebar:
        st.title("Schulwege")

        for route in routes:
            if st.button(route["name"], width=300):
                default_args = {}
                if "default_args" in route:
                    default_args = route["default_args"]
                router.redirect(*router.build(route["view"].__name__, default_args))
