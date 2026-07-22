
{{ config(materialized='table') }}
-- MARTS: punctuality per line
-- Compares actual vehicle timestamps at stops against the GTFS schedule.
select
    line,
    count(*)                                            as measurements,
    round(avg(delay_minutes), 2)                        as avg_delay_min,
    round(median(delay_minutes), 2)                     as median_delay_min,
    round(100.0 * sum(case when delay_minutes <= 1 and delay_minutes >= -1 then 1 else 0 end)
          / count(*), 1)                                as pct_on_time,
    round(100.0 * sum(case when delay_minutes > 3 then 1 else 0 end)
          / count(*), 1)                                as pct_late,
    round(100.0 * sum(case when delay_minutes < -3 then 1 else 0 end)
          / count(*), 1)                                as pct_early
from {{ ref('int_vehicle_delays') }}
group by line
having count(*) >= 10
order by avg_delay_min desc

