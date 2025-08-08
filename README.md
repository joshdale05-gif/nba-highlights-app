# NBA Highlights Scraper & Dashboard

This project collects recent NBA highlight videos from YouTube and serves them up in an interactive Streamlit dashboard.  It consists of two components:

1. **Scraper** – A Python script (`src/scheduler.py`) that queries the YouTube Data API for highlight videos based off a set of search terms, obtains basic statistics (title, channel, publication date and view count) for each video, and stores the data in a PostgreSQL database.  The scraper is designed to be run on an hourly schedule using a Render cron job.
2. **Dashboard** – A Streamlit application (`src/app_streamlit.py`) that reads the data from the database and lets you filter by date and view count.  It displays a data table and a simple bar chart of the view counts.

The repository is configured with a **Render Blueprint** (`render.yaml`) that provisions both a web service to host the Streamlit app and a cron job to run the scraper every hour.  It also provisions a free Postgres database and wires up the connection string and secrets using environment variables.

## Local Development

1.  Install Python 3.9+ and [pipenv](https://pipenv.pypa.io/) or use a virtual environment of your choice.
2.  Create a virtual environment and install dependencies:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  Copy the example environment file and update it with your secrets:

    ```bash
    cp .env.example .env
    # then edit .env to set YOUTUBE_API_KEY and DATABASE_URL
    ```

4.  Initialise the database and run the scraper once:

    ```bash
    python -m src.scheduler
    ```

5.  Launch the Streamlit dashboard:

    ```bash
    streamlit run src/app_streamlit.py
    ```

The dashboard will be available at `http://localhost:8501`.  Adjust the filters to explore your collected highlights.

## Deployment on Render

This repository contains a `render.yaml` blueprint which tells Render how to deploy the application.  When you connect this repo in Render:

1.  Render will provision a free **Postgres** database named `nba-highlights-db` and inject its connection string into the environment variable `DATABASE_URL` for both the web service and the cron job.
2.  Render will ask you to supply the value of `YOUTUBE_API_KEY` during the initial deployment.  You can obtain a key by creating a project in the [Google Cloud Console](https://console.developers.google.com/) and enabling the YouTube Data API v3.
3.  The web service runs `streamlit run src/app_streamlit.py` on port `$PORT` and serves the dashboard.
4.  The cron job runs `python src/scheduler.py` every hour to keep the database up to date.

You can deploy via the Render UI by selecting **New &rarr; Blueprint**, pointing it at this repo, and following the prompts.  Alternatively, use the Render CLI for automated deployments.

## Files and Directories

```
├── render.yaml            # Render Blueprint describing the services, cron job and database
├── requirements.txt       # Python dependencies
├── .env.example           # Example environment file
├── seeds/
│   └── keywords.json      # List of search phrases for the YouTube scraper
└── src/
    ├── __init__.py        # Marks src as a Python package
    ├── app_streamlit.py   # Streamlit dashboard
    ├── config.py          # Loads configuration from environment variables
    ├── database.py        # SQLAlchemy models and session helper
    └── scheduler.py       # Scraper script for the cron job
```

Feel free to extend the dashboard, add more sophisticated filters, or enrich the data model with additional statistics.