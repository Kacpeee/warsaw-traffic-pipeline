"""
Build and test the dbt models.

This DAG has no schedule of its own: it is triggered whenever either
source dataset is refreshed. That guarantees the delay models are only
rebuilt once both live positions and the timetable are up to date.
"""
from datetime import timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from warsaw_alerts import DEFAULT_ARGS
from warsaw_datasets import GTFS_DATA, POSITIONS_DATA

DBT = "cd /opt/warsaw/warsaw_dbt && dbt"

with DAG(
    dag_id="warsaw_build_models",
    description="Transform and validate data with dbt",
    schedule=[GTFS_DATA, POSITIONS_DATA],   # dataset-driven, no cron
    catchup=False,
    default_args={**DEFAULT_ARGS, "retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["traffic", "dbt", "transform"],
) as dag:

    # A refreshed GTFS feed can drop stops that historical rows still
    # reference, leaving orphaned foreign keys in the incremental models.
    # Rebuilding the dependent facts keeps them consistent with the current
    # timetable; at this scale a full refresh costs a few seconds.
    run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"{DBT} run --profiles-dir . --no-partial-parse "
            f"--select stg_gtfs_stops+ stg_gtfs_routes+ stg_gtfs_trips+ --full-refresh && "
            f"{DBT} run --profiles-dir . --no-partial-parse"
        ),
    )

    test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT} test --profiles-dir . --no-partial-parse",
    )

    docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"{DBT} docs generate --profiles-dir . --no-partial-parse",
    )

    run >> test >> docs
