-- STAGING: GTFS scheduled stop times
-- Largest GTFS file (~500 MB). We join to trips (already parsed and typed)
-- and keep only the service dates we actually collected GPS positions for.
{{ config(materialized='table') }}

with collected_dates as (
    select distinct cast(vehicle_time as date) as d
    from {{ ref('stg_positions') }}
),

relevant_trips as (
    select trip_id, service_date
    from {{ ref('stg_gtfs_trips') }}
    where service_date in (select d from collected_dates)
),

raw_times as (
    select
        trip_id,
        try_cast(stop_sequence as integer) as stop_sequence,
        stop_id,
        arrival_time as arrival_time_raw
    from read_csv('../gtfs/stop_times.txt', header=true, all_varchar=true)
)

select
    rt.trip_id,
    rt.stop_sequence,
    rt.stop_id,
    t.service_date,
    rt.arrival_time_raw,
    -- GTFS allows times past 24h ('25:30:00' = 1:30 next morning),
    -- so build the timestamp from the service date plus intervals.
    t.service_date::timestamp
        + interval (try_cast(split_part(rt.arrival_time_raw, ':', 1) as integer)) hour
        + interval (try_cast(split_part(rt.arrival_time_raw, ':', 2) as integer)) minute
        + interval (try_cast(split_part(rt.arrival_time_raw, ':', 3) as integer)) second
        as scheduled_arrival
from raw_times rt
join relevant_trips t on rt.trip_id = t.trip_id
