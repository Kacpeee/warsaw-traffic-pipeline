import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)

n = con.execute("select count(*) from int_route_segments").fetchone()[0]
m = con.execute("select count(*) from mart_slowest_segments").fetchone()[0]
print(f"segments observed: {n:,}   segments ranked: {m:,}\n")

print("=== SLOWEST SEGMENTS (most time lost vs schedule) ===")
print(f"{'line':>5} | {'from':22} | {'to':22} | {'obs':>4} | {'act':>5} | {'sched':>5} | {'lost':>5}")
print("-" * 90)
for r in con.execute("""
    select line, from_stop, to_stop, observations,
           avg_actual_min, avg_scheduled_min, avg_lost_min
    from mart_slowest_segments limit 15
""").fetchall():
    print(f"{r[0]:>5} | {str(r[1])[:22]:22} | {str(r[2])[:22]:22} | {r[3]:>4} | {r[4]:>5} | {r[5]:>5} | {r[6]:>5}")

print("\n=== FASTEST (ahead of schedule) ===")
for r in con.execute("""
    select line, from_stop, to_stop, observations, avg_lost_min
    from mart_slowest_segments order by avg_lost_min limit 5
""").fetchall():
    print(f"{r[0]:>5} | {str(r[1])[:22]:22} | {str(r[2])[:22]:22} | {r[3]:>4} | {r[4]:>5}")
