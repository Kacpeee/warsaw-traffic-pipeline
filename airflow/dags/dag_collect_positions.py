"""
Collect live vehicle positions.

Buses and trams are exposed as separate feeds, so they are collected in
parallel and merged afterwards - a fan-out / fan-in pattern.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import PythonOperator
from warsaw_alerts import DEFAULT_ARGS
from warsaw_datasets import POSITIONS_DATA

with DAG(
    dag_id="warsaw_collect_positions",
    description="Poll live vehicle positions from the ZTM API",
    start_date=datetime(2026, 7, 1),
    schedule="0 * * * *",              # hourly
    catchup=False,
    max_active_runs=1,                 # never overlap collectors
    default_args={
        **DEFAULT_ARGS,
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
        # a collector run should take ~55 min; anything longer means it is
        # stuck retrying a dead connection rather than gathering data
        "execution_timeout": timedelta(minutes=70),
    },
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

    def check_freshness(**context):
        """Fail loudly if the run produced little or no data.

        A collector can exit cleanly while returning nothing (API outage,
        empty response), so success of the task alone is not proof that data
        arrived. This asserts a plausible row count instead.
        """
        import glob
        import os
        import time

        cutoff = time.time() - 3600
        recent = [
            f for f in glob.glob("/opt/warsaw/data/positions_*")
            if os.path.getmtime(f) > cutoff
        ]
        if not recent:
            raise ValueError("no position files written in the last hour")

        total = sum(os.path.getsize(f) for f in recent)
        print(f"{len(recent)} fresh file(s), {total / 1e6:.1f} MB")
        if total < 10_000:
            raise ValueError(f"suspiciously little data collected: {total} bytes")

    freshness = PythonOperator(
        task_id="check_freshness",
        python_callable=check_freshness,
    )

    merged = EmptyOperator(
        task_id="positions_ready",
        outlets=[POSITIONS_DATA],      # publishes only after checks pass
    )

    [collect_buses, collect_trams] >> freshness >> merged
