-- STAGING: clean raw vehicle positions
--
-- Historical data lives in CSV, new runs write Parquet (smaller, typed,
-- ~5x better compression). Both are read through glob patterns and unioned.
{{ config(
    materialized='incremental',
    unique_key=['vehicle_number', 'vehicle_time'],
    incremental_strategy='delete+insert'
) }}

with csv_source as (
    select
        try_cast(fetch_time as timestamp)   as fetch_time,
        try_cast(vehicle_time as timestamp) as vehicle_time,
        vehicle_number,
        line,
        brigade,
        try_cast(vehicle_type as integer)   as vehicle_type,
        try_cast(lat as double)             as lat,
        try_cast(lon as double)             as lon
    from read_csv(
        '../data/positions_*.csv',
        header = false,
        all_varchar = true,
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
    where fetch_time <> 'fetch_time'
),

parquet_source as (
    select
        fetch_time,
        vehicle_time,
        vehicle_number,
        line,
        brigade,
        cast(vehicle_type as integer) as vehicle_type,
        lat,
        lon
    from read_parquet('../data/positions_*.parquet')
),

combined as (
    select * from csv_source
    union all
    select * from parquet_source
),

cleaned as (
    select *
    from combined
    where lat is not null
      and lon is not null
      and vehicle_time is not null
      and lat between 51.9 and 52.5
      and lon between 20.7 and 21.3
),

-- A stationary vehicle reports the same vehicle_time on every poll, so keep
-- only the first observation of each (vehicle, timestamp) pair.
deduplicated as (
    select fetch_time, vehicle_time, vehicle_number, line, brigade,
           vehicle_type, lat, lon
    from (
        select *,
               row_number() over (
                   partition by vehicle_number, vehicle_time
                   order by fetch_time
               ) as rn
        from cleaned
    )
    where rn = 1
)

select * from deduplicated
{% if is_incremental() %}
  where fetch_time > (select coalesce(max(fetch_time), timestamp '1970-01-01') from {{ this }})
{% endif %}
