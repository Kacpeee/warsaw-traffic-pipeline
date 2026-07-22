import duckdb
con = duckdb.connect("dev.duckdb")
print(con.execute("""
    select
        case
            when abs(delay_minutes) <= 3  then 'a: |d| <= 3 min'
            when abs(delay_minutes) <= 10 then 'b: 3-10 min'
            when abs(delay_minutes) <= 20 then 'c: 10-20 min'
            else 'd: > 20 min (podejrzane)'
        end as bucket,
        count(*) as n
    from int_vehicle_delays
    group by 1 order by 1
""").fetchall())
