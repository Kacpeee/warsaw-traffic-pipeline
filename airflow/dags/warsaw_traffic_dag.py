"""
Warsaw traffic pipeline DAG
1. Collect live vehicle positions from the ZTM API
2. Run dbt models (staging -> intermediate -> marts)
3. Run dbt tests
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

default_args = {
    "owner": "kacper",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="warsaw_traffic_pipeline",
    description="Collect Warsaw transit positions and model them with dbt",
    default_args=default_args,
    start_date=datetime(2026, 7, 1),
    schedule="0 * * * *",          # every hour
    catchup=False,
    tags=["traffic", "dbt", "portfolio"],
) as dag:

    collect = BashOperator(
        task_id="collect_positions",
        bash_command=(
            "cd /opt/warsaw && "
            "python collect.py"
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "cd /opt/warsaw/warsaw_dbt && "
            "dbt run --profiles-dir . --no-partial-parse"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "cd /opt/warsaw/warsaw_dbt && "
            "dbt test --profiles-dir . --no-partial-parse"
        ),
    )

    collect >> dbt_run >> dbt_test
