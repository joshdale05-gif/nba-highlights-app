"""
Database models and helper functions using SQLAlchemy.

This module defines the ``Highlight`` model used to store metadata for each
YouTube video.  It also exposes a ``SessionLocal`` factory for producing
scoped sessions and an ``init_db`` function to create tables on-demand.
"""

from __future__ import annotations

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Import configuration using an absolute import.  When modules are executed
# as scripts (e.g. via ``streamlit run src/app_streamlit.py``), relative imports
# are not allowed because there is no package context.  Import directly
# from the ``config`` module instead of using a relative import.
from config import DATABASE_URL


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


# Create engine and session factory.  psycopg2 is not yet compatible with
# Python 3.13, so we prefer the psycopg (v3) driver if a plain
# ``postgresql://`` URL is provided.  SQLAlchemy determines the driver
# based on the URL scheme.  If the URL begins with ``postgresql://``,
# replace the scheme with ``postgresql+psycopg://`` to explicitly select
# the psycopg driver.  This ensures compatibility on Python 3.13.
db_url: str = DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(db_url, echo=False, future=True)
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