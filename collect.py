'''Collect live vehicle positions from the Warsaw ZTM API.

Buses and trams are separate feeds, so the mode is passed as an argument and
both can be collected in parallel. Each run writes its own Parquet file:
appending to a single file is not possible with columnar formats, and a glob
pattern lets DuckDB read the whole directory transparently.
'''
import argparse
import os
from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq
import warsaw_data_api
from dotenv import load_dotenv
import time

OUT_DIR = 'data'
SCHEMA = pa.schema([
    ('fetch_time', pa.timestamp('s')),
    ('vehicle_number', pa.string()),
    ('line', pa.string()),
    ('brigade', pa.string()),
    ('vehicle_type', pa.int8()),
    ('lat', pa.float64()),
    ('lon', pa.float64()),
    ('vehicle_time', pa.timestamp('s')),
])

parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['buses', 'trams'], default='buses')
parser.add_argument('--iterations', type=int, default=55)
parser.add_argument('--interval', type=int, default=60)
args = parser.parse_args()

load_dotenv()
ztm = warsaw_data_api.ztm(apikey=os.getenv('WARSAW_DATA_API_KEY'))
fetch = ztm.get_buses_location if args.mode == 'buses' else ztm.get_trams_location

os.makedirs(OUT_DIR, exist_ok=True)
rows = []
FLUSH_EVERY = 10   # write a batch periodically: an interrupted run would
                   # otherwise lose everything buffered in memory


def flush(buffer):
    if not buffer:
        return
    stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    path = os.path.join(OUT_DIR, f'positions_{args.mode}_{stamp}.parquet')
    pq.write_table(pa.Table.from_pylist(buffer, schema=SCHEMA), path,
                   compression='zstd')
    print(f'wrote {len(buffer):,} rows to {path} '
          f'({os.path.getsize(path) / 1e6:.1f} MB)', flush=True)
    buffer.clear()

for i in range(args.iterations):
    now = datetime.now().replace(microsecond=0)
    try:
        vehicles = fetch()
    except Exception as exc:
        print(f'[{now}] {args.mode}: fetch failed: {exc}', flush=True)
        time.sleep(args.interval)
        continue

    for v in vehicles:
        rows.append({
            'fetch_time': now,
            'vehicle_number': str(v.vehicle_number),
            'line': str(v.lines),
            'brigade': str(v.brigade),
            'vehicle_type': int(v.type) if v.type is not None else None,
            'lat': float(v.location.latitude),
            'lon': float(v.location.longitude),
            'vehicle_time': v.time,
        })

    print(f'[{now}] {args.mode}: {len(vehicles)} vehicles '
          f'({i + 1}/{args.iterations}, buffered {len(rows)})', flush=True)

    if (i + 1) % FLUSH_EVERY == 0:
        flush(rows)

    if i < args.iterations - 1:
        time.sleep(args.interval)

flush(rows)
print('done:', args.mode)
