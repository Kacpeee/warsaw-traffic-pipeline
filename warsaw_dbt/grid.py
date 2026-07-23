import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)
n, mn, mx = con.execute("""
    select count(*), min(avg_speed_kmh), max(avg_speed_kmh) from mart_speed_grid
""").fetchone()
print(f"komorek siatki: {n:,}   predkosc od {mn} do {mx} km/h")
print("\nnajwolniejsze komorki:")
for r in con.execute("""
    select round(cell_lat,4), round(cell_lon,4), observations, avg_speed_kmh, pct_crawling
    from mart_speed_grid where observations >= 50
    order by avg_speed_kmh limit 8
""").fetchall():
    print(f"  {r[0]}, {r[1]}   obs={r[2]:>5}   {r[3]:>5} km/h   pelza {r[4]}%")
