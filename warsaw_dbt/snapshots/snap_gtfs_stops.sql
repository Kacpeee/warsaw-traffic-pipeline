{% snapshot snap_gtfs_stops %}
{{
    config(
      target_schema='main',
      unique_key='stop_id',
      strategy='check',
      check_cols=['stop_name', 'stop_lat', 'stop_lon'],
    )
}}

-- Tracks stop relocations and renames. Useful when a stop moves during
-- roadworks: historical analyses can still resolve the position that was
-- valid at the time.
select
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    town_name
from {{ ref('stg_gtfs_stops') }}

{% endsnapshot %}
