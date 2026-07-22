import duckdb
con = duckdb.connect("dev.duckdb")

print("=== PUNKTUALNOSC WG GODZINY ===")
print("godz | pomiary | sred_opozn | mediana | %spoz | sred_odchyl")
for r in con.execute("select * from mart_punctuality_by_hour").fetchall():
    print(f"{r[0]:>4} | {r[1]:>7} | {r[2]:>10} | {r[3]:>7} | {r[4]:>5} | {r[5]}")

print("\n=== NAJGORSZE PRZYSTANKI ===")
print("przystanek                | pomiary | linie | sred_opozn | max  | %spoz")
for r in con.execute("select stop_name, measurements, lines_served, avg_delay_min, max_delay_min, pct_late from mart_worst_stops limit 12").fetchall():
    print(f"{str(r[0])[:24]:24} | {r[1]:>7} | {r[2]:>5} | {r[3]:>10} | {r[4]:>4} | {r[5]}")

print("\n=== PREDKOSC WG GODZINY (agregat po wszystkich liniach) ===")
print("godz | pomiary | sred_predkosc | %pelzania")
for r in con.execute("""
    select hour_of_day, sum(measurements) as n,
           round(sum(avg_speed_kmh*measurements)/sum(measurements),1) as avg_kmh,
           round(sum(pct_crawling*measurements)/sum(measurements),1) as pct_crawl
    from mart_speed_by_hour group by 1 order by 1
""").fetchall():
    print(f"{r[0]:>4} | {r[1]:>7} | {r[2]:>13} | {r[3]}")
