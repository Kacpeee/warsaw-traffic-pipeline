-- MARTS: vehicle positions sampled for animation
--
-- Animating every ping would push hundreds of thousands of points into the
-- browser. Positions are bucketed into 5-minute frames and one position per
-- vehicle per frame is kept, which is enough to show movement while staying
-- responsive.
{{ config(materialized='table') }}

with sampled as (
    select
        vehicle_number,
        line,
        vehicle_type,
        lat,
        lon,
        vehicle_time,
        -- floor the timestamp to a 5-minute bucket
        time_bucket(interval 15 minute, vehicle_time) as frame_time,
        row_number() over (
            partition by vehicle_number,
                         time_bucket(interval 15 minute, vehicle_time)
            order by vehicle_time
        ) as rn
    from {{ ref('stg_positions') }}
    -- restrict to a single service day: mixing days would interleave frames
    -- with the same clock time but different dates
    where cast(vehicle_time as date) = (
        select max(cast(vehicle_time as date)) from {{ ref('stg_positions') }}
    )
)

select
    frame_time,
    strftime(frame_time, '%H:%M')            as frame_label,
    extract(hour from frame_time)            as hour_of_day,
    vehicle_number,
    line,
    case vehicle_type when 1 then 'Bus' when 2 then 'Tram' else 'Other' end
                                             as mode,
    lat,
    lon
from sampled
where rn = 1
order by frame_time
