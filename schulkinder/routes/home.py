from streamlit_router import StreamlitRouter
import streamlit as st


def home(router: StreamlitRouter):
    st.title("Willkommen zu Schulkinder")
    st.write("Dies ist die Startseite der Schulkinder-App.")
