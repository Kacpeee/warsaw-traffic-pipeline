-- STAGING: GTFS routes (dimension)
-- route_id is not numeric for all modes (rail 'E-1', metro 'M1'), so read as text.
select
    route_id,
    route_short_name as line,
    route_long_name,
    try_cast(route_type as integer) as route_type
from read_csv('../gtfs/routes.txt', header=true, all_varchar=true)
