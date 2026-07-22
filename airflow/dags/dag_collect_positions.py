"""
Collect live vehicle positions.

Buses and trams are exposed as separate feeds, so they are collected in
parallel and merged afterwards - a fan-out / fan-in pattern.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from warsaw_datasets import POSITIONS_DATA

with DAG(
    dag_id="warsaw_collect_positions",
    description="Poll live vehicle positions from the ZTM API",
    start_date=datetime(2026, 7, 1),
    schedule="0 * * * *",              # hourly
    catchup=False,
    max_active_runs=1,                 # never overlap collectors
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["traffic", "source"],
) as dag:

    collect_buses = BashOperator(
        task_id="collect_buses",
        bash_command="cd /opt/warsaw && python collect.py --mode buses",
    )

    collect_trams = BashOperator(
        task_id="collect_trams",
        bash_command="cd /opt/warsaw && python collect.py --mode trams",
    )

    merged = EmptyOperator(
        task_id="positions_ready",
        outlets=[POSITIONS_DATA],      # publishes only after both succeed
    )

    [collect_buses, collect_trams] >> merged
