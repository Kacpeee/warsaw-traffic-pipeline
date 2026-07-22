{% snapshot snap_gtfs_routes %}
{{
    config(
      target_schema='main',
      unique_key='route_id',
      strategy='check',
      check_cols=['line', 'route_long_name', 'route_type'],
    )
}}

-- Tracks changes to the published route definitions over time: renamed lines,
-- rerouted services or new routes appearing in the feed.
select
    route_id,
    line,
    route_long_name,
    route_type
from {{ ref('stg_gtfs_routes') }}

{% endsnapshot %}
