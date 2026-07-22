import duckdb
con = duckdb.connect("dev.duckdb")

print("--- przyklad brygad z GPS ---")
print(con.execute("""
    select line, brigade, count(*) as n
    from stg_positions
    where cast(vehicle_time as date) = date '2026-07-22'
    group by line, brigade order by n desc limit 5
""").fetchall())

print("--- przyklad brygad z GTFS ---")
print(con.execute("""
    select r.line, t.brigade, count(*) as n
    from stg_gtfs_trips t
    join stg_gtfs_routes r on t.route_id = r.route_id
    where t.service_date = date '2026-07-22'
    group by r.line, t.brigade order by n desc limit 5
""").fetchall())

print("--- ile par (linia,brygada) z GPS ma odpowiednik w GTFS ---")
print(con.execute("""
    with gps as (
        select distinct line, brigade
        from stg_positions
        where cast(vehicle_time as date) = date '2026-07-22'
    ),
    gtfs as (
        select distinct r.line, t.brigade
        from stg_gtfs_trips t
        join stg_gtfs_routes r on t.route_id = r.route_id
        where t.service_date = date '2026-07-22'
    )
    select
        (select count(*) from gps) as gps_pairs,
        (select count(*) from gtfs) as gtfs_pairs,
        (select count(*) from gps join gtfs using (line, brigade)) as matched
""").fetchall())
