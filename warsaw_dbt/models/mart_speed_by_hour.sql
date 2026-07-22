
{{ config(materialized='table') }}
-- MARTS: speed by line and hour
-- Combines the movement data with time of day to expose congestion patterns.
select
    line,
    extract(hour from vehicle_time)                     as hour_of_day,
    count(*)                                            as measurements,
    round(avg(speed_kmh), 1)                            as avg_speed_kmh,
    round(median(speed_kmh), 1)                         as median_speed_kmh,
    round(100.0 * sum(case when speed_kmh < 5 then 1 else 0 end)
          / count(*), 1)                                as pct_crawling
from {{ ref('int_vehicle_moves') }}
group by 1, 2
having count(*) >= 10
order by line, hour_of_day

