with flights as (

    select * from {{ ref('fct_flight') }}

),

dates as (

    select * from {{ ref('dim_date') }}

),

aggregated as (

    select
        flights.date_key,
        flights.origin_code,
        count(*) as flight_count,
        count(*) filter (flights.is_cancelled) as cancelled_count,
        count(*) filter (flights.is_departure_delayed) as departure_delayed_count,
        avg(flights.departure_delay_minutes) as avg_departure_delay_minutes,
        max(flights.departure_delay_minutes) as max_departure_delay_minutes,
        avg(flights.origin_precipitation_in) as avg_precipitation_in,
        min(flights.origin_visibility_miles) as min_visibility_miles,
        max(flights.origin_wind_speed_mph) as max_wind_speed_mph
    from flights
    group by flights.date_key, flights.origin_code

)

select
    dates.date_day,
    dates.calendar_month,
    dates.month_name,
    dates.day_name,
    dates.is_weekend,
    dates.is_holiday,
    dates.holiday_name,
    aggregated.origin_code,
    aggregated.flight_count,
    aggregated.cancelled_count,
    aggregated.departure_delayed_count,
    round(100.0 * aggregated.cancelled_count / aggregated.flight_count, 2)
        as cancellation_rate_pct,
    round(100.0 * aggregated.departure_delayed_count / aggregated.flight_count, 2)
        as departure_delay_rate_pct,
    round(aggregated.avg_departure_delay_minutes, 2) as avg_departure_delay_minutes,
    aggregated.max_departure_delay_minutes,
    round(aggregated.avg_precipitation_in, 4) as avg_precipitation_in,
    aggregated.min_visibility_miles,
    aggregated.max_wind_speed_mph
from aggregated
inner join dates
    on aggregated.date_key = dates.date_key
order by dates.date_day, aggregated.origin_code
