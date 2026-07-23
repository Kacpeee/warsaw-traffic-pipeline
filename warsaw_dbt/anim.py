import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)
n, frames, veh = con.execute("""
    select count(*), count(distinct frame_time), count(distinct vehicle_number)
    from mart_animation_frames
""").fetchone()
print(f"punktow: {n:,}   klatek: {frames}   pojazdow: {veh:,}")
print("\nrozklad punktow na klatke:")
for r in con.execute("""
    select frame_label, count(*) as n
    from mart_animation_frames group by 1 order by 1 limit 10
""").fetchall():
    print(f"  {r[0]}  {r[1]:>5}")
