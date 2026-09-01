with spine as (

    select unnest(generate_series(
        (select min(flight_date) from {{ ref('stg_flight') }}),
        (select max(flight_date) from {{ ref('stg_flight') }}),
        interval 1 day
    ))::date as date_day

),

holidays as (

    select
        holiday_date,
        holiday_name
    from {{ ref('us_holidays_2013') }}

)

select
    {{ surrogate_key(['spine.date_day']) }} as date_key,
    spine.date_day,
    year(spine.date_day) as calendar_year,
    quarter(spine.date_day) as calendar_quarter,
    month(spine.date_day) as calendar_month,
    monthname(spine.date_day) as month_name,
    day(spine.date_day) as day_of_month,
    dayofweek(spine.date_day) as day_of_week,
    dayname(spine.date_day) as day_name,
    weekofyear(spine.date_day) as week_of_year,
    dayofweek(spine.date_day) in (0, 6) as is_weekend,
    holidays.holiday_date is not null as is_holiday,
    holidays.holiday_name
from spine
left join holidays
    on spine.date_day = holidays.holiday_date
