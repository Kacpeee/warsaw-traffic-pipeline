import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)
print("--- rozklad fetch_time w ostatnich 3h (z pliku, nie z modelu) ---")
q = """
select cast(fetch_time as timestamp) as ft, count(*) as n
from read_csv('../raw_positions.csv', header=false, all_varchar=true,
    columns={'fetch_time':'VARCHAR','vehicle_number':'VARCHAR','line':'VARCHAR',
             'brigade':'VARCHAR','vehicle_type':'VARCHAR','lat':'VARCHAR',
             'lon':'VARCHAR','vehicle_time':'VARCHAR'})
where fetch_time <> 'fetch_time'
group by 1 order by 1 desc limit 10
"""
for r in con.execute(q).fetchall():
    print(f"{r[0]}  {r[1]:>5}")
