import duckdb
con = duckdb.connect("dev.duckdb")

checks = [
    ("positions",        "select count(*) from stg_positions"),
    ("collected dates",  "select distinct cast(vehicle_time as date) from stg_positions"),
    ("gtfs stops",       "select count(*) from stg_gtfs_stops"),
    ("gtfs routes",      "select count(*) from stg_gtfs_routes"),
    ("gtfs trips",       "select count(*) from stg_gtfs_trips"),
    ("trip dates",       "select distinct service_date from stg_gtfs_trips order by 1 limit 5"),
    ("stop_times",       "select count(*) from stg_gtfs_stop_times"),
]
for name, q in checks:
    print(f"{name:18} -> {con.execute(q).fetchall()}")
