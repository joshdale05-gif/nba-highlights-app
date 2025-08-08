"""
YouTube scraper for collecting NBA highlight videos.

This script queries the YouTube Data API v3 for a set of search phrases
contained in ``seeds/keywords.json``.  For each term it retrieves a page
of recent videos (limited by ``RESULTS_PER_PAGE``) sorted by publication date.
It then fetches statistics for the discovered videos and stores them in
the database.  Existing records are updated in place (upsert on primary
key).  The script is designed to be run regularly (e.g., hourly) via
Render cron jobs or other schedulers.

Before running this script, ensure the environment variable
``YOUTUBE_API_KEY`` is set.  Without a valid API key the Google API client
will fail to authenticate.
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Iterable, List, Dict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.exc import SQLAlchemyError

from .config import YOUTUBE_API_KEY, RESULTS_PER_PAGE
from .database import init_db, Highlight, SessionLocal


def load_keywords() -> List[str]:
    """Load search phrases from the seeds/keywords.json file."""
    # Compute path relative to this file
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    keywords_file = os.path.join(base, "seeds", "keywords.json")
    with open(keywords_file, "r", encoding="utf-8") as f:
        return json.load(f)


def search_videos(youtube, term: str) -> List[Dict[str, str]]:
    """Search YouTube for a single term and return basic video data.

    Args:
        youtube: Authorized API client from googleapiclient.discovery.build
        term: Search term to query

    Returns:
        A list of dicts containing video_id, title, channel_title and published_at.
    """
    request = youtube.search().list(
        q=term,
        part="snippet",
        type="video",
        maxResults=RESULTS_PER_PAGE,
        order="date",
    )
    response = request.execute()
    results = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        results.append(
            {
                "video_id": item["id"]["videoId"],
                "title": snippet["title"],
                "channel_title": snippet["channelTitle"],
                "published_at": datetime.datetime.strptime(
                    snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        )
    return results


def fetch_statistics(youtube, video_ids: List[str]) -> Dict[str, int]:
    """Retrieve view counts for a list of video IDs.

    Args:
        youtube: Authorized API client
        video_ids: List of YouTube video IDs

    Returns:
        A mapping from video_id to view count (int).  Missing values default to 0.
    """
    if not video_ids:
        return {}
    # The API allows up to 50 IDs per request
    chunks: List[List[str]] = [video_ids[i : i + 50] for i in range(0, len(video_ids), 50)]
    stats: Dict[str, int] = {}
    for chunk in chunks:
        ids_str = ",".join(chunk)
        request = youtube.videos().list(
            part="statistics",
            id=ids_str,
        )
        response = request.execute()
        for item in response.get("items", []):
            vid = item["id"]
            view_count = int(item.get("statistics", {}).get("viewCount", 0))
            stats[vid] = view_count
    return stats


def fetch_highlights() -> List[Dict[str, object]]:
    """Orchestrate the search across all keywords and attach statistics."""
    if not YOUTUBE_API_KEY:
        raise SystemExit("Environment variable YOUTUBE_API_KEY is not set.")
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    keywords = load_keywords()
    all_videos: List[Dict[str, object]] = []
    seen_ids: set[str] = set()
    # Perform a search for each term
    for term in keywords:
        try:
            videos = search_videos(youtube, term)
        except HttpError as e:
            print(f"Error querying term '{term}': {e}")
            continue
        for v in videos:
            vid = v["video_id"]
            if vid not in seen_ids:
                seen_ids.add(vid)
                all_videos.append(v)
    # Attach view counts
    stats = fetch_statistics(youtube, [v["video_id"] for v in all_videos])
    for v in all_videos:
        v["views"] = stats.get(v["video_id"], 0)
    return all_videos


def update_database(records: Iterable[Dict[str, object]]) -> None:
    """Persist highlight records to the database.

    Uses SQLAlchemy's session.merge() to perform an upsert on the primary key.
    Accepts any iterable of record dictionaries.
    """
    init_db()
    # Convert iterable to a list so we can count rows before iterating
    recs = list(records)
    session = SessionLocal()
    try:
        for rec in recs:
            obj = Highlight(
                video_id=rec["video_id"],
                title=rec["title"],
                channel_title=rec.get("channel_title"),
                published_at=rec.get("published_at"),
                views=rec.get("views"),
            )
            session.merge(obj)
        session.commit()
        print(f"Upserted {len(recs)} records")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    highlights = fetch_highlights()
    update_database(highlights)