import duckdb
con = duckdb.connect("dev.duckdb")
print("dopasowan:", con.execute("select count(*) from int_vehicle_delays").fetchone()[0])
print("\nlinia | pomiary | sred | mediana | %punkt | %spoz | %wczes")
for r in con.execute("select * from mart_line_punctuality limit 15").fetchall():
    print(f"{r[0]:>5} | {r[1]:>7} | {r[2]:>4} | {r[3]:>7} | {r[4]:>6} | {r[5]:>5} | {r[6]}")
