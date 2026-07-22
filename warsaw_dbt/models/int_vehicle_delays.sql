-- INTERMEDIATE: match live GPS positions to scheduled stop times
--
-- Approach:
--   1. join positions to GTFS trips via (line, brigade)
--   2. for each position, look only at stops served by that vehicle's trips
--   3. keep the nearest stop within a radius (vehicle is "at" that stop)
--   4. delay = actual timestamp - scheduled arrival
--
-- Only stops within STOP_RADIUS_M are considered a match, and only the
-- closest scheduled arrival in time is kept per position.
{{ config(
    materialized='incremental',
    unique_key=['vehicle_number', 'actual_time'],
    incremental_strategy='delete+insert'
) }}

with valid_positions as (
    select
        vehicle_number,
        line,
        brigade,
        vehicle_time,
        lat,
        lon,
        cast(vehicle_time as date) as service_date
    from {{ ref('stg_positions') }}
    -- drop stale positions: the API returns last-known location, which can be
    -- days or even years old for vehicles that stopped reporting
    where vehicle_time >= current_date - interval 2 day
    {% if is_incremental() %}
      -- only match positions collected since the last run
      and vehicle_time > (select coalesce(max(actual_time), timestamp '1970-01-01') from {{ this }})
    {% endif %}
),

trips_with_line as (
    select
        t.trip_id,
        t.service_date,
        t.brigade,
        r.line
    from {{ ref('stg_gtfs_trips') }} t
    join {{ ref('stg_gtfs_routes') }} r
      on t.route_id = r.route_id
),

-- candidate stops: every scheduled stop of every trip run by this line+brigade
candidates as (
    select
        st.trip_id,
        p.vehicle_number,
        p.line,
        p.brigade,
        p.vehicle_time,
        p.lat,
        p.lon,
        st.stop_id,
        s.stop_name,
        s.stop_lat,
        s.stop_lon,
        st.scheduled_arrival,
        -- distance in meters (equirectangular approximation)
        sqrt(
            pow((p.lat - s.stop_lat) * 111320.0, 2) +
            pow((p.lon - s.stop_lon) * 111320.0 * cos(radians(p.lat)), 2)
        ) as meters_to_stop,
        abs(date_diff('second', st.scheduled_arrival, p.vehicle_time)) as abs_time_gap
    from valid_positions p
    join trips_with_line t
      on p.line = t.line
     and p.brigade = t.brigade
     and p.service_date = t.service_date
    join {{ ref('stg_gtfs_stop_times') }} st
      on st.trip_id = t.trip_id
    join {{ ref('stg_gtfs_stops') }} s
      on st.stop_id = s.stop_id
),

-- keep only positions physically at a stop, and pick the single best match
ranked as (
    select
        *,
        row_number() over (
            partition by vehicle_number, vehicle_time
            order by abs_time_gap, meters_to_stop
        ) as rn
    from candidates
    where meters_to_stop <= 100          -- vehicle is at the stop
      and abs_time_gap <= 900            -- within 15 min of schedule
)

select
    trip_id,
    vehicle_number,
    line,
    brigade,
    stop_id,
    stop_name,
    vehicle_time                as actual_time,
    scheduled_arrival,
    round(meters_to_stop)       as meters_to_stop,
    -- positive = late, negative = early
    date_diff('second', scheduled_arrival, vehicle_time) as delay_seconds,
    round(date_diff('second', scheduled_arrival, vehicle_time) / 60.0, 1) as delay_minutes
from ranked
where rn = 1
