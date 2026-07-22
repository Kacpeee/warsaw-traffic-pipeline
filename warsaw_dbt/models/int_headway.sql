-- INTERMEDIATE: headway between consecutive vehicles
--
-- Headway is the gap between successive vehicles of the same line at the same
-- stop. It matters more to passengers than schedule adherence: regular
-- 8-minute gaps beat a 'punctual' timetable where two buses arrive together
-- and nothing comes for 20 minutes (bunching).
--
-- A stationary vehicle pings its position every minute, so raw arrivals are
-- deduplicated into visits first: consecutive pings of the same vehicle at the
-- same stop are collapsed into one arrival unless separated by a long gap.
{{ config(materialized='table') }}

with pings as (
    select distinct
        line,
        stop_id,
        stop_name,
        vehicle_number,
        actual_time
    from {{ ref('int_vehicle_delays') }}
),

-- mark the start of a new visit: first ping, or a ping more than 10 minutes
-- after the previous one from the same vehicle at the same stop
flagged as (
    select
        *,
        case
            when date_diff('second',
                           lag(actual_time) over w,
                           actual_time) > 600
              or lag(actual_time) over w is null
            then 1 else 0
        end as is_new_visit
    from pings
    window w as (partition by line, stop_id, vehicle_number order by actual_time)
),

visits as (
    select
        line,
        stop_id,
        stop_name,
        vehicle_number,
        -- one row per visit: the moment the vehicle first appeared at the stop
        min(actual_time) as arrival_time
    from (
        select *, sum(is_new_visit) over (
            partition by line, stop_id, vehicle_number order by actual_time
        ) as visit_id
        from flagged
    )
    group by line, stop_id, stop_name, vehicle_number, visit_id
),

gaps as (
    select
        line,
        stop_id,
        stop_name,
        vehicle_number,
        arrival_time,
        lag(vehicle_number) over w as prev_vehicle,
        lag(arrival_time)   over w as prev_arrival,
        date_diff('second', lag(arrival_time) over w, arrival_time) / 60.0
            as headway_minutes
    from visits
    window w as (partition by line, stop_id order by arrival_time)
)

select
    line,
    stop_id,
    stop_name,
    vehicle_number,
    prev_vehicle,
    prev_arrival,
    arrival_time,
    round(headway_minutes, 2) as headway_minutes,
    -- vehicles arriving less than 2 minutes apart are effectively bunched
    headway_minutes < 2       as is_bunched
from gaps
where prev_arrival is not null
  and vehicle_number <> prev_vehicle
  and headway_minutes between 0.1 and 120
