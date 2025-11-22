import streamlit as st
from streamlit_router import StreamlitRouter


@st.fragment
def header(router: StreamlitRouter, title: str, redirect=None):
    """
    Displays a header with an optional redirect button.
    Args:
        router: The StreamlitRouter instance.
        title: The title to display in the header.
        redirect: An optional dictionary containing:
            - "route": The route to redirect to.
            - "args": The arguments for the route.
            - "desc": The description for the redirect button.

    """

    if redirect:
        assert "route" in redirect, "redirect must contain 'route' key"
        assert "args" in redirect, "redirect must contain 'args' key"
        assert "desc" in redirect, "redirect must contain 'desc' key"
        if st.button(redirect["desc"], type="tertiary"):
            router.redirect(*router.build(redirect["route"], redirect["args"]))

    st.markdown(f"## {title}")
