import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv
import warsaw_data_api

load_dotenv()
ztm = warsaw_data_api.ztm(apikey=os.getenv("WARSAW_DATA_API_KEY"))

OUT = "raw_positions.csv"
INTERVAL = 60          # sekundy miedzy odpytaniami
ITERATIONS = 60        # ile razy odpytac (60 x 60s = 1 godzina)

# naglowek tylko jesli plik nie istnieje
write_header = not os.path.exists(OUT)
with open(OUT, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    if write_header:
        writer.writerow(["fetch_time", "vehicle_number", "line", "brigade",
                         "type", "lat", "lon", "vehicle_time"])

    for i in range(ITERATIONS):
        fetch_time = datetime.now().isoformat(timespec="seconds")
        try:
            buses = ztm.get_buses_location()
        except Exception as e:
            print(f"[{fetch_time}] blad pobierania: {e}")
            time.sleep(INTERVAL)
            continue

        rows = 0
        with open(OUT, "a", newline="", encoding="utf-8") as f2:
            w = csv.writer(f2)
            for v in buses:
                w.writerow([
                    fetch_time,
                    v.vehicle_number,
                    v.lines,
                    v.brigade,
                    v.type,
                    v.location.latitude,
                    v.location.longitude,
                    v.time.isoformat() if v.time else "",
                ])
                rows += 1
        print(f"[{fetch_time}] zapisano {rows} pojazdow  (iteracja {i+1}/{ITERATIONS})")

        if i < ITERATIONS - 1:
            time.sleep(INTERVAL)

print("Gotowe. Dane w", OUT)
