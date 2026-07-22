-- INTERMEDIATE: travel time between consecutive stops
--
-- Instead of asking which stops are late, this measures where time is actually
-- lost: the segment between two consecutive stops of the same trip. Comparing
-- the observed travel time against the scheduled one isolates the bottlenecks.
{{ config(materialized='table') }}

with observed as (
    select
        d.line,
        d.brigade,
        d.vehicle_number,
        d.stop_id,
        d.stop_name,
        d.actual_time,
        d.scheduled_arrival,
        lag(d.stop_id)           over w as prev_stop_id,
        lag(d.stop_name)         over w as prev_stop_name,
        lag(d.actual_time)       over w as prev_actual,
        lag(d.scheduled_arrival) over w as prev_scheduled
    from {{ ref('int_vehicle_delays') }} d
    window w as (
        -- partition by trip: a vehicle finishing one trip and starting the
        -- next would otherwise produce a bogus segment across the turnaround
        partition by d.trip_id, d.vehicle_number
        order by d.actual_time
    )
),

segments as (
    select
        line,
        prev_stop_id                                     as from_stop_id,
        prev_stop_name                                   as from_stop,
        stop_id                                          as to_stop_id,
        stop_name                                        as to_stop,
        vehicle_number,
        prev_actual                                      as departed_at,
        actual_time                                      as arrived_at,
        date_diff('second', prev_actual, actual_time) / 60.0    as actual_minutes,
        date_diff('second', prev_scheduled, scheduled_arrival) / 60.0
                                                         as scheduled_minutes
    from observed
    where prev_stop_id is not null
      and prev_stop_id <> stop_id
      -- a station can span several platforms sharing one name; a vehicle
      -- hopping between them (typically between trips) is not a segment
      and prev_stop_name <> stop_name
)

select
    *,
    round(actual_minutes - scheduled_minutes, 2) as lost_minutes
from segments
where actual_minutes between 0.2 and 30
  and scheduled_minutes between 0.2 and 30
  and abs(actual_minutes - scheduled_minutes) <= 15
