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
    file_hash = Column(String, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    taken_at = Column(DateTime)
    description = Column(String)
    people = Column(String)  # comma separated list of recognized people


_engine = None
_Session = None


def init_db(db_path: str | Path) -> None:
    """Initialise the SQLite database.

    Tuning notes:
    - Enable pool_pre_ping to recycle dead connections.
    - Increase pool size and overflow for bursty workloads.
    - Disable SQLite thread check to allow usage across Flask threads.
    """
    global _engine, _Session
    _engine = create_engine(
        f"sqlite:///{db_path}",
        pool_size=10,
        max_overflow=30,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(_engine)
    # Ensure newer columns exist for existing DBs
    try:
        from sqlalchemy import inspect, text

        insp = inspect(_engine)
        cols = {c["name"] for c in insp.get_columns("photos")}
        if "file_hash" not in cols:
            with _engine.connect() as conn:
                conn.execute(text("ALTER TABLE photos ADD COLUMN file_hash VARCHAR"))
                conn.commit()
        # Create unique index if not exists (SQLite allows multiple NULLs)
        with _engine.connect() as conn:
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_photos_file_hash ON photos(file_hash)"))
            conn.commit()
    except Exception:
        # Best-effort; ignore if migrations are not possible
        pass

    _Session = sessionmaker(bind=_engine, expire_on_commit=False)


def get_session() -> Session:
    if _Session is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _Session()
