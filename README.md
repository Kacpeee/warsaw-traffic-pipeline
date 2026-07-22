[README (1).md](https://github.com/user-attachments/files/30285414/README.1.md)
# Warsaw Transit Pipeline

[![dbt CI](https://github.com/Kacpeee/warsaw-traffic-pipeline/actions/workflows/dbt-ci.yml/badge.svg)](https://github.com/Kacpeee/warsaw-traffic-pipeline/actions/workflows/dbt-ci.yml)
[![Python CI](https://github.com/Kacpeee/warsaw-traffic-pipeline/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Kacpeee/warsaw-traffic-pipeline/actions/workflows/python-ci.yml)

A data pipeline that collects **live vehicle positions** from Warsaw's public
transport API, joins them with the **GTFS timetable**, and measures how the
network actually performs: speed, punctuality, service regularity and where
journey time is lost.

![Average delay per stop](docs/dashboard.png)

---

## What the data shows

| Metric | Night (1–3 AM) | Midday (1–2 PM) |
| --- | --- | --- |
| Average speed | 19.3 km/h | 13.4 km/h |
| Time spent below 5 km/h | 26% | 35% |

Median delay across the network stays under a minute, but the averages hide the
interesting part:

- **Trams are the most predictable** services (irregularity index ≈ 0.45),
  helped by segregated track.
- **Replacement lines (Z33, Z-9, Z26) are the least predictable** — an
  irregularity index near 1.0 means the standard deviation of the wait equals
  its mean.
- **Line 2 bunches most often**: 17% of arrivals come less than two minutes
  after the previous vehicle.
- Some segments are **systematically underestimated by the timetable** — the
  stretch to PKP Wola is scheduled for 3 minutes and consistently takes 6.

---

## Stack

**Python** (API collector, Parquet output) · **dbt** (17 models, 2 snapshots,
60 tests) · **DuckDB** · **Airflow** (dataset-driven orchestration) ·
**Streamlit** (dashboard) · **GitHub Actions** (CI)

---

## Architecture

```
ZTM API   ──►  positions_*.parquet  ──┐
                                      ├──►  staging  ──►  intermediate  ──►  marts
GTFS feed ──►  *.txt  ────────────────┘     (typed,       (speed, delays,   (per line,
                                             cleaned,      headway,          hour, stop,
                                             deduped)      segments)         segment)
```

Three DAGs, connected by Airflow **datasets** rather than a shared schedule:

| DAG | Trigger | Does |
| --- | --- | --- |
| `warsaw_refresh_gtfs` | daily, 04:00 | downloads the timetable feed |
| `warsaw_collect_positions` | hourly | polls buses and trams in parallel, checks freshness |
| `warsaw_build_models` | when **either** dataset updates | runs dbt build, tests, docs |

The third DAG has no schedule of its own — it reacts to upstream data becoming
available, which is the part a cron job cannot express.

---

## How the matching works

Live positions carry a line and a brigade (running board); GTFS trips carry the
same pair. That is the join key, and it resolves for **99.7%** of observed
vehicles.

A position within **100 m** of a scheduled stop counts as an arrival. The delay
is the difference between the observed and scheduled timestamp, keeping the
closest match in time rather than in space — sorting by distance first matched
vehicles to the wrong run of the same route.

**Headway** (the gap between consecutive vehicles at a stop) needed a second
correction: a stationary vehicle re-reports its position every minute, so
consecutive pings are collapsed into one *visit* before measuring gaps. That
single change moved the measured bunching rate from 11.9% to 1.4%.

---

## Models

| Layer | Models |
| --- | --- |
| staging | positions, GTFS stops / routes / trips / stop_times |
| dimension | calendar spine |
| intermediate | `int_vehicle_moves` (speed), `int_vehicle_delays` (schedule adherence), `int_headway` (gaps), `int_route_segments` (stop-to-stop travel time) |
| marts | speed per line, speed per hour, punctuality per line, punctuality per hour, worst stops, line regularity, slowest segments |
| snapshots | route and stop definitions, tracked over time |

`stg_positions` and `int_vehicle_delays` are **incremental** — a full rebuild
takes 2.6 s, an incremental run 0.2 s.

---

## Data quality

Real feeds are messy. Tests and filters handle:

- **stale positions** — the API returns a last-known location, sometimes years old
- **duplicate pings** — stationary vehicles repeat the same timestamp
  (caught by a composite-key test that failed on 11,879 rows)
- **GPS jumps** producing impossible speeds
- **GTFS times past midnight** (`25:30:00` belongs to the previous service day)
- **mixed-type identifiers** (`E-1`, `M1`) breaking CSV type inference
- **multi-platform stations** — one name, several `stop_id`s, which produced
  phantom "segments" between a stop and itself

60 dbt tests cover null checks, accepted ranges, referential integrity between
GTFS tables, and composite key uniqueness.

---

## Run it

```bash
conda create -n traffic python=3.11 -y && conda activate traffic
pip install -r requirements.txt

echo "WARSAW_DATA_API_KEY=your_key" > .env       # register at api.um.warszawa.pl
curl -LfO 'https://mkuran.pl/gtfs/warsaw.zip' && unzip warsaw.zip -d gtfs/

python collect.py --mode buses                   # collect live positions
cd warsaw_dbt && dbt build                       # models, tests, snapshots
```

Dashboard:

```bash
streamlit run dashboard.py
```

Scheduled, end to end:

```bash
cd airflow && docker compose up -d               # Airflow at localhost:8080
```

---

## Limitations

Collection runs locally: `api.um.warszawa.pl` refuses connections from foreign
data centres (verified against a Spanish VPS — DNS resolves, but ICMP and HTTPS
both time out), so a Polish network is a hard requirement. The machine has to be
running for data to arrive, which leaves gaps in coverage.

Per-stop and per-segment statistics rest on small samples and should be read as
directional rather than conclusive.
