
{{ config(materialized='table') }}
-- INTERMEDIATE layer: compute vehicle movement
-- For each vehicle, compare consecutive positions over time
-- and derive distance, elapsed time and speed.
with positions as (
    select
        vehicle_number, line, brigade, vehicle_type,
        vehicle_time, lat, lon,
        -- previous position of the same vehicle (ordered by time)
        lag(lat)          over w as prev_lat,
        lag(lon)          over w as prev_lon,
        lag(vehicle_time) over w as prev_time
    from {{ ref('stg_positions') }}
    window w as (partition by vehicle_number order by vehicle_time)
),
moves as (
    select
        vehicle_number, line, brigade, vehicle_type,
        prev_time, vehicle_time,
        lat, lon,
        -- elapsed time in seconds
        date_diff('second', prev_time, vehicle_time) as seconds_diff,
        -- distance in meters (equirectangular approximation)
        sqrt(
            pow((lat - prev_lat) * 111320.0, 2) +
            pow((lon - prev_lon) * 111320.0 * cos(radians(lat)), 2)
        ) as meters_diff
    from positions
    where prev_time is not null
),
with_speed as (
    select
        vehicle_number, line, brigade, vehicle_type,
        prev_time, vehicle_time, lat, lon, seconds_diff, meters_diff,
        -- speed in km/h (m/s * 3.6)
        case
            when seconds_diff > 0
            then round((meters_diff / seconds_diff) * 3.6, 1)
            else null
        end as speed_kmh
    from moves
    where seconds_diff between 1 and 600   -- keep gaps from 1s to 10 min
)
select *
from with_speed
where speed_kmh is not null
  and speed_kmh <= 100    -- drop physically impossible speeds (GPS jumps)

