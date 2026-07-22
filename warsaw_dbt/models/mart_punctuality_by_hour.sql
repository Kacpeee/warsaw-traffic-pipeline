
{{ config(materialized='table') }}
-- MARTS: punctuality by hour of day
-- Shows how delays build up during peak hours versus off-peak.
select
    extract(hour from actual_time)                      as hour_of_day,
    count(*)                                            as measurements,
    round(avg(delay_minutes), 2)                        as avg_delay_min,
    round(median(delay_minutes), 2)                     as median_delay_min,
    round(100.0 * sum(case when delay_minutes > 3 then 1 else 0 end)
          / count(*), 1)                                as pct_late,
    round(avg(abs(delay_minutes)), 2)                   as avg_abs_deviation_min
from {{ ref('int_vehicle_delays') }}
group by 1
having count(*) >= 30
order by 1

