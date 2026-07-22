"""Shared failure handling for the Warsaw pipeline DAGs."""
import logging
from datetime import datetime
from pathlib import Path

ALERT_LOG = Path("/opt/warsaw/alerts.log")


def alert_on_failure(context):
    """Record a failed task so problems are visible outside the Airflow UI.

    In a production setup this is where a Slack webhook or PagerDuty call
    would go; writing to a file keeps the project self-contained while still
    demonstrating the callback mechanism.
    """
    ti = context["task_instance"]
    msg = (
        f"{datetime.now().isoformat(timespec='seconds')} "
        f"FAILED dag={ti.dag_id} task={ti.task_id} "
        f"run={context['run_id']} try={ti.try_number}"
    )
    logging.error("ALERT: %s", msg)
    try:
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ALERT_LOG.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except OSError as exc:
        logging.error("could not write alert log: %s", exc)


DEFAULT_ARGS = {
    "owner": "kacper",
    "on_failure_callback": alert_on_failure,
}
