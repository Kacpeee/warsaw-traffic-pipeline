# Warsaw Public Transport Speed Pipeline

A data pipeline that collects **live vehicle positions** from Warsaw's public
transport API and computes the **average speed of each line** using a layered
dbt model (staging -> intermediate -> marts) on DuckDB.

## What it does

1. **Collect** – a Python collector polls the Warsaw ZTM API every minute and
   appends live vehicle positions (GPS, line, timestamp) to a raw CSV.
2. **Model** – dbt transforms the raw data through three layers:
   - `stg_positions` – clean and type the raw data, drop invalid coordinates
   - `int_vehicle_moves` – compute distance, elapsed time and **speed**
     between consecutive positions of each vehicle (window functions)
   - `mart_line_speed` – aggregate to average speed per line
3. **Test** – dbt tests validate data quality (not-null, uniqueness).

## Tech stack

- **Python** – data collection from a REST API
- **dbt** – layered SQL modeling, tests, documentation, lineage
- **DuckDB** – local analytical database
- *(planned)* Apache Airflow – orchestration; OpenMetadata – cataloging

## Architecture

\\\
Warsaw ZTM API
      |
      v  (collect.py, every 60s)
raw_positions.csv        <- raw layer
      |
      v  (dbt)
stg_positions            <- staging: cleaned & typed
      |
      v
int_vehicle_moves        <- intermediate: speed per movement
      |
      v
mart_line_speed          <- marts: average speed per line
\\\

## How to run

\\\ash
# 1. Environment
conda create -n traffic python=3.11 -y
conda activate traffic
pip install requests python-dotenv warsaw-data-api dbt-duckdb duckdb

# 2. Set your API key (get one at https://api.um.warszawa.pl/)
echo "WARSAW_DATA_API_KEY=your_key" > .env

# 3. Collect data (runs ~1h, polling every minute)
python collect.py

# 4. Run the dbt pipeline
cd warsaw_dbt
dbt run
dbt test
\\\

## Data quality notes

Real GPS data is noisy. The pipeline handles this by:
- filtering positions outside a Warsaw bounding box,
- dropping movements with implausible speeds (GPS jumps),
- keeping only time gaps between 1s and 10 minutes.

## Notes

Vehicle positions carry their own timestamp, which can lag behind the fetch
time (e.g. parked vehicles at night). Speed is computed from the vehicle
timestamp, not the fetch time. Collecting during daytime peak hours yields
the most meaningful movement data.
