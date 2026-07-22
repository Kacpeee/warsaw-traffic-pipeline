"""
Refresh the static GTFS timetable.

The ZTM feed is republished once a day, so this runs on its own daily
schedule - independent of the hourly position collection.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from warsaw_datasets import GTFS_DATA

with DAG(
    dag_id="warsaw_refresh_gtfs",
    description="Download the daily GTFS schedule feed",
    start_date=datetime(2026, 7, 1),
    schedule="0 4 * * *",              # every day at 04:00
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["traffic", "gtfs", "source"],
) as dag:

    download = BashOperator(
        task_id="download_gtfs",
        bash_command=(
            "cd /opt/warsaw/gtfs && "
            "curl -sLfO 'https://mkuran.pl/gtfs/warsaw.zip' && "
            "unzip -oq warsaw.zip && "
            "rm -f warsaw.zip && "
            "ls -la stops.txt trips.txt"
        ),
        outlets=[GTFS_DATA],           # publishes the dataset
    )
