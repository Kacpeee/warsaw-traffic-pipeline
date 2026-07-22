-- STAGING: GTFS stops (dimension)
-- Read everything as text: stop_id values like 'R-1300' break type inference.
select
    stop_id,
    stop_name,
    try_cast(stop_lat as double) as stop_lat,
    try_cast(stop_lon as double) as stop_lon,
    town_name
from read_csv('../gtfs/stops.txt', header=true, all_varchar=true)
where try_cast(stop_lat as double) is not null
  and try_cast(stop_lon as double) is not null
