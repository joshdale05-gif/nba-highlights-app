"""
Streamlit dashboard for exploring NBA highlight videos.

This app reads highlight metadata from the database and displays it in a
filterable table alongside a bar chart of view counts.  Use the controls
in the sidebar to adjust the time range and minimum view count.
"""

from __future__ import annotations

import datetime
from typing import List

import pandas as pd
import streamlit as st
from sqlalchemy.orm import sessionmaker

# When this script is executed via ``streamlit run src/app_streamlit.py``,
# it is not part of a package, so relative imports fail.  Import the
# database module using an absolute name instead of a relative one.
from database import Highlight, engine


def load_data(days_back: int) -> pd.DataFrame:
    """Load highlights from the database within the given date range.

    Args:
        days_back: Number of days to look back from today (UTC).

    Returns:
        Pandas DataFrame with columns: video_id, title, channel_title,
        published_at, views
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days_back)
        results: List[Highlight] = (
            session.query(Highlight)
            .filter(Highlight.published_at >= cutoff)
            .order_by(Highlight.published_at.desc())
            .all()
        )
        data = [
            {
                "video_id": h.video_id,
                "title": h.title,
                "channel_title": h.channel_title,
                "published_at": h.published_at,
                "views": h.views or 0,
            }
            for h in results
        ]
        return pd.DataFrame(data)
    finally:
        session.close()


def main() -> None:
    st.set_page_config(page_title="NBA Highlights Dashboard", layout="wide")
    st.title("NBA Highlights Dashboard")
    st.write("Explore recent NBA highlight videos scraped from YouTube.")

    with st.sidebar:
        st.header("Filters")
        days_back = st.slider("Days back", min_value=1, max_value=30, value=7)
        min_views = st.number_input(
            "Minimum views", min_value=0, value=0, step=1000,
            help="Filter out videos with fewer than this number of views."
        )

    df = load_data(days_back)
    if df.empty:
        st.warning("No data available. Try expanding the date range or run the scraper.")
        return

    # Apply filters
    df_filtered = df[df["views"] >= min_views]

    st.subheader(f"Showing {len(df_filtered)} videos published in the last {days_back} days")
    st.dataframe(df_filtered, use_container_width=True)

    # Bar chart of views
    chart_df = df_filtered.set_index("title")
    # If there are many rows, limit to top 20 for readability
    chart_df = chart_df.sort_values("views", ascending=False).head(20)
    st.bar_chart(chart_df["views"])


if __name__ == "__main__":
    main()