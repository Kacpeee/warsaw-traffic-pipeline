-- MARTS: speed aggregated onto a spatial grid
--
-- Point-level speeds are noisy and unreadable on a map. Snapping each
-- observation to a ~300 m grid cell and averaging exposes the corridors where
-- traffic actually slows down, which is invisible in per-line aggregates.
{{ config(materialized='table') }}

with binned as (
    select
        -- ~300 m cells: 0.0027 deg latitude, adjusted for longitude convergence
        round(lat / 0.0027) * 0.0027                          as cell_lat,
        round(lon / 0.0044) * 0.0044                          as cell_lon,
        extract(hour from vehicle_time)                       as hour_of_day,
        speed_kmh,
        vehicle_type
    from {{ ref('int_vehicle_moves') }}
)

select
    cell_lat,
    cell_lon,
    count(*)                                   as observations,
    round(avg(speed_kmh), 1)                   as avg_speed_kmh,
    round(median(speed_kmh), 1)                as median_speed_kmh,
    round(100.0 * sum(case when speed_kmh < 5 then 1 else 0 end)
          / count(*), 1)                       as pct_crawling,
    count(distinct vehicle_type)               as modes
from binned
group by cell_lat, cell_lon
having count(*) >= 20     -- a cell needs enough passes to be meaningful
   -- Cells where vehicles are stationary almost all the time are depots and
   -- terminals, not congestion. Real traffic still moves between stops, so a
   -- cell crawling over 80% of the time is parking, not a bottleneck.
   and 100.0 * sum(case when speed_kmh < 5 then 1 else 0 end) / count(*) <= 80
order by observations desc
