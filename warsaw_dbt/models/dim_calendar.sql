-- DIMENSION: calendar
-- Generated date spine covering the collected period, so time-based analyses
-- can distinguish weekdays from weekends and school terms from holidays.
{{ config(materialized='table') }}

with bounds as (
    select
        cast(min(vehicle_time) as date) as start_date,
        cast(max(vehicle_time) as date) as end_date
    from {{ ref('stg_positions') }}
),

spine as (
    select unnest(generate_series(
        (select start_date from bounds),
        (select end_date from bounds),
        interval 1 day
    ))::date as date_day
)

select
    date_day,
    extract(year  from date_day)            as year,
    extract(month from date_day)            as month,
    extract(day   from date_day)            as day,
    extract(dow   from date_day)            as day_of_week,   -- 0 = Sunday
    strftime(date_day, '%A')                as day_name,
    extract(dow from date_day) in (0, 6)    as is_weekend,
    -- Polish summer school holidays: July and August
    extract(month from date_day) in (7, 8)  as is_school_holiday
from spine
