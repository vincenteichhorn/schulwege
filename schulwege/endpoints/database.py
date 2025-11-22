import os
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from schulwege.models.base import Base


def get_engine():

    @st.cache_resource
    def _create_engine():
        db_url = os.getenv("SQL_DATABASE_URL", "sqlite:///data/schulwege/schulwege.db")
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(db_url, echo=False, connect_args={"check_same_thread": False})
        return engine

    return _create_engine()


def get_session():
    engine = get_engine()
    SessionLocal = scoped_session(sessionmaker(bind=engine))
    return SessionLocal()


def init_db(engine):
    from schulwege.models.project import Project
    from schulwege.models.location import Location
    from schulwege.models.segment import Segment

    Base.metadata.create_all(engine)
