import streamlit as st
from typing import List


def info_badges(infos: List[str], columns=True, spacing: int = 4):
    """Display a list of info badges."""
    if columns:
        badges = f" <span style='margin-right: {spacing}px;'></span>".join(
            [f":blue-badge[{info}]" for info in infos]
        )
        st.markdown(badges, unsafe_allow_html=True)
    else:
        for info in infos:
            st.markdown(f":blue-badge[{info}]")
