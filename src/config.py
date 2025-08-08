"""
Configuration loader for the NBA highlights project.

This module reads environment variables using python-dotenv to support both
development and production deployments.  The following variables are used:

* ``DATABASE_URL`` – SQLAlchemy connection string for your database.  Defaults to a local SQLite
  file for development.  In production, Render injects a Postgres connection
  string via the Render Blueprint.
* ``YOUTUBE_API_KEY`` – API key for the YouTube Data API v3.
* ``RESULTS_PER_PAGE`` – Number of search results to request per keyword (default 25).

On import, the dotenv file at the project root is loaded automatically if it exists.
"""

import os
from dotenv import load_dotenv


# Load variables from a .env file if present
load_dotenv()

# Database URL (use SQLite by default for local development)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/highlights.db")

# YouTube Data API key (must be provided for the scraper to function)
YOUTUBE_API_KEY: str | None = os.getenv("YOUTUBE_API_KEY")

# Maximum number of results to fetch per search term when scraping
try:
    RESULTS_PER_PAGE: int = int(os.getenv("RESULTS_PER_PAGE", "25"))
except ValueError:
    RESULTS_PER_PAGE = 25