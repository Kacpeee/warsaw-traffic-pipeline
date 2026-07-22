import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)

n, b = con.execute("""
    select count(*), sum(case when is_bunched then 1 else 0 end)
    from int_headway
""").fetchone()
print(f"headway observations: {n:,}   bunched: {b:,} ({100*b/n:.1f}%)\n")

hdr = "line  | obs  | avg  | median | stddev | %bunch | index"
print("=== LEAST REGULAR LINES ===")
print(hdr)
for r in con.execute("select * from mart_line_regularity limit 12").fetchall():
    print(f"{r[0]:>5} | {r[1]:>4} | {r[2]:>4} | {r[3]:>6} | {r[4]:>6} | {r[5]:>6} | {r[6]}")

print("\n=== MOST REGULAR LINES ===")
print(hdr)
for r in con.execute("select * from mart_line_regularity order by irregularity_index limit 5").fetchall():
    print(f"{r[0]:>5} | {r[1]:>4} | {r[2]:>4} | {r[3]:>6} | {r[4]:>6} | {r[5]:>6} | {r[6]}")
