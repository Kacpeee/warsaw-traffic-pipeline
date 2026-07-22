import duckdb
con = duckdb.connect("dev.duckdb")

n = con.execute("select count(*) from int_vehicle_delays").fetchone()[0]
print("dopasowanych pozycji do przystankow:", n)

if n:
    print("\n--- przyklady ---")
    rows = con.execute("""
        select line, brigade, stop_name, actual_time, scheduled_arrival,
               meters_to_stop, delay_minutes
        from int_vehicle_delays
        order by abs(delay_minutes) desc
        limit 10
    """).fetchall()
    print("linia|bryg| przystanek           | rzeczywisty        | rozkladowy         | m   | opozn")
    for r in rows:
        print(f"{r[0]:>5}|{r[1]:>4}| {str(r[2])[:20]:20} | {r[3]} | {r[4]} | {r[5]:>3} | {r[6]}")

    print("\n--- statystyki opoznien (minuty) ---")
    print(con.execute("""
        select round(avg(delay_minutes),1) as srednia,
               round(median(delay_minutes),1) as mediana,
               round(min(delay_minutes),1) as min,
               round(max(delay_minutes),1) as max
        from int_vehicle_delays
    """).fetchall())
