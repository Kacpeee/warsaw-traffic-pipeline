-- MARTS: service regularity per line
--
-- Combines average headway with its variability. A low standard deviation means
-- passengers can rely on a steady rhythm; a high one means unpredictable waits
-- even if the average looks fine.
{{ config(materialized='table') }}

select
    line,
    count(*)                                        as observations,
    round(avg(headway_minutes), 2)                  as avg_headway_min,
    round(median(headway_minutes), 2)               as median_headway_min,
    round(stddev(headway_minutes), 2)               as headway_stddev,
    round(100.0 * sum(case when is_bunched then 1 else 0 end)
          / count(*), 1)                            as pct_bunched,
    -- coefficient of variation: regularity independent of frequency
    round(stddev(headway_minutes) / nullif(avg(headway_minutes), 0), 2)
                                                    as irregularity_index
from {{ ref('int_headway') }}
group by line
having count(*) >= 20
   and avg(headway_minutes) <= 20   -- only frequent services, where regularity matters
order by irregularity_index desc
