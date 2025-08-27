"""Database models and session management for Photo Trails."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Photo(Base):
    """Model representing an ingested photo."""

    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    taken_at = Column(DateTime)
    description = Column(String)
    people = Column(String)  # comma separated list of recognized people


_engine = None
_Session = None


def init_db(db_path: str | Path) -> None:
    """Initialise the SQLite database."""
    global _engine, _Session
    _engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(_engine)
    _Session = sessionmaker(bind=_engine)


def get_session() -> Session:
    if _Session is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _Session()
