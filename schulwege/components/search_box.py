from typing import Any, Callable, Dict
import streamlit as st
from st_keyup import st_keyup

from schulwege.models.location import Location


def search_box(
    label: str,
    search_callback: Callable[[str], Dict[int, Any]],
    topN: int = 5,
    format_func: Callable[[Any], str] = None,
    key: str = "search_box",
) -> str:
    """
    Displays a search box for searching projects.
    """

    st.markdown(
        """
            <style>
                .st-key-search_box_options label {
                    display: none;
                }
            </style>
        """,
        unsafe_allow_html=True,
    )

    if "search_box_input" not in st.session_state:
        st.session_state.search_box_input = ""
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = None

    if format_func is None:
        format_func = lambda x: str(x)

    search_input = st_keyup(
        label=label,
        key="search_box_input",
        debounce=100,
    )
    result = search_input
    if len(search_input) >= 3:
        search_results = search_callback(search_input)
        option_list = {i: itm for i, itm in enumerate(search_results[:topN])}
        st.session_state[key] = search_input
        if len(option_list) == 0:
            st.error(f"Keine Sucheergebnisse gefunden.")
        elif len(option_list) == 1:
            st.session_state[f"{key}_selected"] = list(option_list.keys())[0]
        else:
            st.session_state[f"{key}_selected"] = st.pills(
                "Search Results:",
                default=None,
                options=option_list.keys(),
                format_func=lambda x: format_func(option_list[x]),
                key="search_box_options",
                label_visibility="collapsed",
            )
        if st.session_state[f"{key}_selected"] is not None and len(option_list) > 0:
            result = option_list[st.session_state[f"{key}_selected"]]
            st.success(f"**Ausgewählt**: {format_func(result)}")
    return result
