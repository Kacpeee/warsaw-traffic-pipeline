-- MARTS: slowest segments in the network
--
-- Ranks stop-to-stop segments by how much longer they take than scheduled.
-- These are the concrete bottlenecks: a segment losing two minutes on every
-- run costs far more across a day than a single late departure.
{{ config(materialized='table') }}

select
    line,
    from_stop,
    to_stop,
    count(*)                                    as observations,
    round(avg(actual_minutes), 2)               as avg_actual_min,
    round(avg(scheduled_minutes), 2)            as avg_scheduled_min,
    round(avg(lost_minutes), 2)                 as avg_lost_min,
    round(max(lost_minutes), 2)                 as worst_lost_min,
    round(100.0 * sum(case when lost_minutes > 1 then 1 else 0 end)
          / count(*), 1)                        as pct_runs_over_schedule
from {{ ref('int_route_segments') }}
group by line, from_stop, to_stop
having count(*) >= 5
order by avg_lost_min desc
