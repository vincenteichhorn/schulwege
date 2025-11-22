import time
from typing import Dict, List, Optional, Tuple, Union
import streamlit as st
from streamlit_router import StreamlitRouter

from schulwege.components.table_upload import table_upload
from schulwege.components.header import header
from schulwege.components.search_box import search_box
from schulwege.endpoints.database import get_session
from schulwege.endpoints.nominatim import get_locations, get_top_location_batch
from schulwege.endpoints.routing import compute_segments
from schulwege.models.location import Location
from schulwege.models.project import Project


def create_project(
    main_location: Location,
    project_name: Optional[str],
    address_list: List[str],
    progress_callback=None,
    force: bool = False,
) -> Optional[Project]:

    locations = get_top_location_batch(
        address_list,
        progress_callback=lambda i, query: (
            progress_callback(f"Geokodierung: {i+1}/{len(address_list)}: {query}")
            if progress_callback
            else None
        ),
    )
    num_errors = sum(1 for loc in locations if loc is None)
    error_locations = [address_list[i] for i, loc in enumerate(locations) if loc is None]
    if num_errors > 0 and not force:
        st.warning(
            f"{num_errors} von {len(address_list)} Adressen konnten nicht gefunden werden. Korrigieren Sie die Adressen oder setzen Sie den Haken 'Fehlerhafte Adressen ignorieren' und probieren Sie es erneut.\n- "
            + "\n- ".join(error_locations)
        )
        return None

    locations = [loc for loc in locations if loc is not None]
    segments = compute_segments(
        main_location,
        locations,
        progress_callback=lambda p: (
            progress_callback(f"Berechnung der Schulwege: {p}") if progress_callback else None
        ),
    )

    session = get_session()
    session.add(main_location)
    session.add_all(segments)
    project = Project(
        name=project_name or main_location.to_string(),
        main_location=main_location,
        segments=segments,
    )
    session.add(project)
    session.commit()
    st.success(f"Projekt '{project.name}' wurde erfolgreich erstellt!")
    if progress_callback:
        progress_callback("Fertig!")
    return project


def new(router: StreamlitRouter):

    st.markdown(
        """
        <style>
            div {
                gap: 8px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    header(
        router,
        "Neues Projekt erstellen",
        redirect={
            "route": "home",
            "args": {},
            "desc": "← Zurück zur Startseite",
        },
    )

    if "form_progress" not in st.session_state:
        st.session_state.form_progress = 1

    main_location = search_box(
        "(1) Schule suchen",
        search_callback=lambda x: get_locations(x, limit=5),
        topN=5,
        format_func=lambda loc: loc.to_string(),
    )
    st.session_state.form_progress = 2 if isinstance(main_location, Location) else 1
    st.markdown("---")

    project_name = st.text_input(
        "(2) Projektname (Optional)",
        key="project_name",
        placeholder=(
            main_location.to_string() if isinstance(main_location, Location) else main_location
        ),
        disabled=st.session_state.form_progress < 2,
    )
    if project_name == "":
        project_name = None
    st.markdown("---")

    df_adresses = table_upload(
        "(3) Adressliste hochladen",
        show_table=True,
        disabled=st.session_state.form_progress < 2,
    )
    st.markdown("---")

    if df_adresses is not None and not df_adresses.empty:
        st.session_state.form_progress = 3

    selected_columns = st.multiselect(
        "(4) Spalte(n) mit Adressen auswählen (Reihenfolge)",
        options=df_adresses.columns.tolist() if df_adresses is not None else [],
        default=(
            df_adresses.columns[0] if df_adresses is not None and not df_adresses.empty else []
        ),
        key="address_column",
        disabled=st.session_state.form_progress < 3,
    )
    if selected_columns:
        example_addresses = (
            df_adresses[selected_columns]
            .head(3)
            .apply(lambda row: " ".join(row.values.astype(str)), axis=1)
            .tolist()
        )
        st.success(
            f"Adressen werden aus {len(selected_columns)} Spalte(n) zusammengesetzt: {' + '.join([f'[{col}]' for col in selected_columns])}\n- "
            + "\n- ".join(example_addresses)
        )

        st.session_state.form_progress = 4

    st.markdown("---")

    agg_address_list = df_adresses.apply(
        lambda row: " ".join(row[selected_columns].values.astype(str)), axis=1
    ).tolist()

    force_errors = st.checkbox(
        "Fehlerhafte Adressen (falls vorhanden) ignorieren und Projekt trotzdem erstellen",
        value=False,
        disabled=st.session_state.form_progress < 4,
    )

    if st.session_state.form_progress >= 4 and st.button("Projekt erstellen"):
        with st.status("Projekt wird erstellt...") as status:
            project = create_project(
                main_location,
                project_name,
                agg_address_list,
                progress_callback=lambda p: status.update(label=p, state="running", expanded=True),
                force=force_errors,
            )
            if project:
                # wait 3s before redirecting
                status.update(label="Weiterleitung...", state="complete", expanded=True)
                time.sleep(3)
                router.redirect(*router.build("project", {"id": project.id}))
