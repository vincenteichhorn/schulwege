import streamlit as st
import pandas as pd


class TableButton:
    def __init__(self, label: str, on_click: callable, key: str | None = None):
        self.label = label
        self.on_click = on_click
        self.key = key

    def render(self, context=st):
        if context.button(self.label, key=self.key):
            self.on_click(self)


def table(df: pd.DataFrame, widths: list[int] | None = None):

    def get_new_cols():
        return st.columns(df.shape[1] if widths is None else widths)

    cols = get_new_cols()
    for col_name in df.columns:
        cols[df.columns.get_loc(col_name)].write(f"**{col_name}**")
    for i, row in df.iterrows():
        cols = get_new_cols()
        for j, (col_name, value) in enumerate(row.items()):
            if isinstance(value, TableButton):
                value.render(context=cols[j])
            else:
                cols[j].write(value)
