"""
Database models and helper functions using SQLAlchemy.

This module defines the ``Highlight`` model used to store metadata for each
YouTube video.  It also exposes a ``SessionLocal`` factory for producing
scoped sessions and an ``init_db`` function to create tables on-demand.
"""

from __future__ import annotations

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL


# SQLAlchemy base class
Base = declarative_base()


class Highlight(Base):
    """Model representing a YouTube highlight video.

    Attributes:
        video_id: unique YouTube video identifier (primary key)
        title: human‑readable title of the video
        channel_title: name of the channel that uploaded the video
        published_at: UTC datetime when the video was published
        views: integer view count at the time of scraping
    """

    __tablename__ = "highlights"

    video_id: str = Column(String, primary_key=True, index=True)
    title: str = Column(String, nullable=False)
    channel_title: str | None = Column(String)
    published_at: "DateTime" = Column(DateTime)
    views: int | None = Column(Integer)


# Create engine and session factory
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Context manager yielding a SQLAlchemy session.

    Usage::

        with get_db_session() as session:
            ...

    Yields a session which is automatically closed on exit.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()