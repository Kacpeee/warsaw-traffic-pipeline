
{{ config(materialized='table') }}
-- STAGING layer: clean raw vehicle positions
-- Source: raw_positions.csv (collected by collect.py)
-- The CSV has no header, so columns are named and typed explicitly here.
with source as (
    select *
    from read_csv(
        '../raw_positions.csv',
        header = false,
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
    where lat is not null
      and lon is not null
      and vehicle_time is not null
      and fetch_time <> 'fetch_time'
      -- Warsaw bounding box: drop obviously invalid coordinates
      and cast(lat as double) between 51.9 and 52.5
      and cast(lon as double) between 20.7 and 21.3
)
select * from cleaned

