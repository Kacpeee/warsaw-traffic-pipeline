# Warsaw Transit Pipeline

Data pipeline that collects **live vehicle positions** from Warsaw's public transport API,
joins them with the **GTFS timetable**, and computes **speed** and **punctuality** per line,
stop and hour.

## Findings

| Metric | Night (1-3 AM) | Midday (1-2 PM) |
|---|---|---|
| Average speed | 19.3 km/h | 13.4 km/h |
| Time spent crawling (<5 km/h) | 26% | 35% |

Median delay across the network is under a minute; suburban lines (L16, L26) run
3-5 minutes late on average.

## Stack

**Python** (API collector) · **dbt** (12 models, 21 tests) · **DuckDB** · **Airflow** (hourly orchestration)

## How it works

\\\
ZTM API  ──►  raw CSV  ──┐
                         ├──►  staging  ──►  intermediate  ──►  marts
GTFS zip ──►  txt files ─┘      (typed,        (speed,          (per line,
                                 cleaned)       delays)          hour, stop)
\\\

**Live positions** are polled every minute and matched to the timetable via
\line + brigade\. A position within 100 m of a scheduled stop counts as an arrival;
the delay is the difference between the actual and scheduled timestamp.

**Models**

| Layer | Models |
|---|---|
| staging | positions, GTFS stops / routes / trips / stop_times |
| intermediate | \int_vehicle_moves\ (speed), \int_vehicle_delays\ (schedule adherence) |
| marts | speed per line, punctuality per line, per hour, worst stops |

## Data quality

Real feeds are messy. The pipeline handles:

- stale positions (the API returns last-known location, sometimes years old)
- GPS jumps producing impossible speeds
- GTFS times past midnight (\25:30:00\)
- mixed-type IDs (\E-1\, \M1\) breaking CSV type inference

## Run it

\\\ash
conda create -n traffic python=3.11 -y && conda activate traffic
pip install requests python-dotenv warsaw-data-api dbt-duckdb duckdb

echo "WARSAW_DATA_API_KEY=your_key" > .env      # get one at api.um.warszawa.pl
curl -LfO 'https://mkuran.pl/gtfs/warsaw.zip' && unzip warsaw.zip -d gtfs/

python collect.py                                # collect live positions
cd warsaw_dbt && dbt run && dbt test             # build and validate models
\\\

Or run the whole thing on a schedule:

\\\ash
cd airflow && docker compose up -d               # Airflow at localhost:8080
\\\

## Notes

Data is collected only while the machine is running, so coverage has gaps.
Per-stop statistics are based on small samples and should be read as directional.
