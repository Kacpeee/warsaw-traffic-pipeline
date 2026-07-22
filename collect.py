"""
Collect live vehicle positions from the Warsaw ZTM API.

Buses and trams are separate feeds, so the mode is passed as an argument
and both can be collected in parallel by the orchestrator.
"""
import argparse
import csv
import os
import time
from datetime import datetime

import warsaw_data_api
from dotenv import load_dotenv

OUT = "raw_positions.csv"
HEADER = ["fetch_time", "vehicle_number", "line", "brigade",
          "type", "lat", "lon", "vehicle_time"]

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["buses", "trams"], default="buses")
parser.add_argument("--iterations", type=int, default=55)
parser.add_argument("--interval", type=int, default=60)
args = parser.parse_args()

load_dotenv()
ztm = warsaw_data_api.ztm(apikey=os.getenv("WARSAW_DATA_API_KEY"))
fetch = ztm.get_buses_location if args.mode == "buses" else ztm.get_trams_location

# write the header only when creating the file
if not os.path.exists(OUT) or os.path.getsize(OUT) == 0:
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(HEADER)

for i in range(args.iterations):
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        vehicles = fetch()
    except Exception as exc:
        print(f"[{ts}] {args.mode}: fetch failed: {exc}")
        time.sleep(args.interval)
        continue

    with open(OUT, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for v in vehicles:
            w.writerow([
                ts, v.vehicle_number, v.lines, v.brigade, v.type,
                v.location.latitude, v.location.longitude,
                v.time.isoformat() if v.time else "",
            ])

    print(f"[{ts}] {args.mode}: wrote {len(vehicles)} vehicles "
          f"({i + 1}/{args.iterations})")

    if i < args.iterations - 1:
        time.sleep(args.interval)

print(f"done: {args.mode}")
