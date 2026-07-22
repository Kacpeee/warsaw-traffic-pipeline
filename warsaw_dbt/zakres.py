import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)
print("--- zakres czasowy pozycji ---")
print(con.execute("""
    select min(vehicle_time) as od, max(vehicle_time) as do, count(*) as n
    from stg_positions
    where vehicle_time >= current_date - interval 7 day
""").fetchall())

print("\n--- pokrycie wg godzin (ostatnie 2 dni) ---")
for r in con.execute("""
    select cast(vehicle_time as date) as dzien,
           extract(hour from vehicle_time) as godz,
           count(*) as n
    from stg_positions
    where vehicle_time >= current_date - interval 2 day
    group by 1,2 order by 1,2
""").fetchall():
    print(f"{r[0]}  {int(r[1]):>2}:00  {r[2]:>7}")
