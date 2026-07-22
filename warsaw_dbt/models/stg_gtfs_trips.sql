-- STAGING: GTFS trips
-- block_short_name is the brigade - the join key to live GPS data.
-- Most trip_ids start with the service date ('2026-07-22:...'), but some
-- (e.g. metro) use a different scheme, so we parse defensively with try_cast.
{{ config(materialized='table') }}

select
    trip_id,
    route_id,
    service_id,
    block_short_name as brigade,
    trip_headsign,
    try_cast(direction_id as integer) as direction_id,
    try_cast(split_part(trip_id, ':', 1) as date) as service_date
from read_csv('../gtfs/trips.txt', header=true, all_varchar=true)
