"""Shared dataset definitions for the Warsaw transit pipeline."""
from airflow.sdk import Asset

GTFS_DATA = Asset("file:///opt/warsaw/gtfs/stops.txt")
POSITIONS_DATA = Asset("file:///opt/warsaw/raw_positions.csv")
