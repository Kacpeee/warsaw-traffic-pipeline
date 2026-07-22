"""
Refresh the static GTFS timetable.

The ZTM feed is republished once a day, so this runs on its own daily
schedule - independent of the hourly position collection.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from warsaw_alerts import DEFAULT_ARGS
from warsaw_datasets import GTFS_DATA

GTFS_URL = "https://mkuran.pl/gtfs/warsaw.zip"
GTFS_DIR = "/opt/warsaw/gtfs"


def download_gtfs():
    """Fetch and unpack the GTFS feed (no external tools required)."""
    import io
    import os
    import zipfile

    import requests

    os.makedirs(GTFS_DIR, exist_ok=True)
    resp = requests.get(GTFS_URL, timeout=300)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(GTFS_DIR)
        names = zf.namelist()

    print(f"extracted {len(names)} files: {', '.join(sorted(names)[:5])} ...")
    for f in ("stops.txt", "trips.txt", "stop_times.txt"):
        path = os.path.join(GTFS_DIR, f)
        print(f"{f}: {os.path.getsize(path) / 1e6:.1f} MB")


with DAG(
    dag_id="warsaw_refresh_gtfs",
    description="Download the daily GTFS schedule feed",
    start_date=datetime(2026, 7, 1),
    schedule="0 4 * * *",              # every day at 04:00
    catchup=False,
    default_args={**DEFAULT_ARGS, "retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["traffic", "gtfs", "source"],
) as dag:

    download = PythonOperator(
        task_id="download_gtfs",
        python_callable=download_gtfs,
        outlets=[GTFS_DATA],           # publishes the dataset
    )
