
{{ config(materialized='table') }}
-- MARTS: worst stops in the network
-- Which stops accumulate the largest delays - useful for spotting bottlenecks.
select
    d.stop_id,
    d.stop_name,
    s.stop_lat,
    s.stop_lon,
    count(*)                                            as measurements,
    count(distinct d.line)                              as lines_served,
    round(avg(d.delay_minutes), 2)                      as avg_delay_min,
    round(max(d.delay_minutes), 2)                      as max_delay_min,
    round(100.0 * sum(case when d.delay_minutes > 3 then 1 else 0 end)
          / count(*), 1)                                as pct_late
from {{ ref('int_vehicle_delays') }} d
join {{ ref('stg_gtfs_stops') }} s on d.stop_id = s.stop_id
group by 1, 2, 3, 4
having count(*) >= 15
order by avg_delay_min desc

