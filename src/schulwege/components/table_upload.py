import pandas as pd
import streamlit as st


def table_upload(label: str, show_table: bool = False, disabled: bool = False) -> pd.DataFrame:
    uploaded_file = st.file_uploader(label=label, type=["csv", "xlsx"], disabled=disabled)

    if uploaded_file is not None:
        try:
            df = (
                pd.read_csv(uploaded_file)
                if uploaded_file.type == "text/csv"
                else pd.read_excel(uploaded_file)
            )
        except Exception as e:
            st.error(f"Fehler beim Einlesen der Datei: {e}")
        if show_table:
            st.dataframe(df, hide_index=True, height=300)
        return df
    return pd.DataFrame()
