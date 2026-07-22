import duckdb
con = duckdb.connect("dev.duckdb", read_only=True)
n, mx = con.execute("select count(*), max(fetch_time) from stg_positions").fetchone()
print(f"wierszy: {n:,}   najnowszy fetch_time: {mx}")
