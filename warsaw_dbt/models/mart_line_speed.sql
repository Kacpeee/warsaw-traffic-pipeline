-- MARTS layer: average speed per line
-- Final analytical output: which lines run fastest/slowest.
select
    line,
    count(*)                        as num_measurements,
    round(avg(speed_kmh), 1)        as avg_speed_kmh,
    round(min(speed_kmh), 1)        as min_speed_kmh,
    round(max(speed_kmh), 1)        as max_speed_kmh
from {{ ref('int_vehicle_moves') }}
group by line
having count(*) >= 5    -- only lines with a meaningful number of measurements
order by avg_speed_kmh desc
