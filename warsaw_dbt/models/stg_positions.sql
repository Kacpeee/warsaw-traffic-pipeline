-- STAGING: clean raw vehicle positions
-- Each collector writes its own file (buses / trams) to avoid concurrent
-- writes to a shared CSV; DuckDB reads them all through a glob pattern.
{{ config(
    materialized='incremental',
    unique_key=['vehicle_number', 'vehicle_time'],
    incremental_strategy='delete+insert'
) }}

with source as (
    select *
    from read_csv(
        '../data/positions_*.csv',
        header = false,
        all_varchar = true,
        union_by_name = false,
        columns = {
            'fetch_time': 'VARCHAR',
            'vehicle_number': 'VARCHAR',
            'line': 'VARCHAR',
            'brigade': 'VARCHAR',
            'vehicle_type': 'VARCHAR',
            'lat': 'VARCHAR',
            'lon': 'VARCHAR',
            'vehicle_time': 'VARCHAR'
        }
    )
),

cleaned as (
    select
        cast(fetch_time as timestamp)      as fetch_time,
        cast(vehicle_time as timestamp)    as vehicle_time,
        vehicle_number,
        line,
        brigade,
        cast(vehicle_type as integer)      as vehicle_type,
        cast(lat as double)                as lat,
        cast(lon as double)                as lon
    from source
    where fetch_time <> 'fetch_time'
      and try_cast(lat as double) is not null
      and try_cast(lon as double) is not null
      and try_cast(vehicle_time as timestamp) is not null
      and try_cast(lat as double) between 51.9 and 52.5
      and try_cast(lon as double) between 20.7 and 21.3
)

select distinct * from cleaned
{% if is_incremental() %}
  where fetch_time > (select coalesce(max(fetch_time), timestamp '1970-01-01') from {{ this }})
{% endif %}
