with flights as (

    select
        *,
        case
            when origin_visibility_miles is null then 'unknown'
            when origin_visibility_miles < 1 then 'visibility under 1 mile'
            when origin_visibility_miles < 3 then 'visibility 1 to 3 miles'
            when origin_visibility_miles < 10 then 'visibility 3 to 10 miles'
            else 'visibility 10 miles or more'
        end as visibility_band,
        case
            when origin_precipitation_in is null then 'unknown'
            when origin_precipitation_in = 0 then 'no precipitation'
            when origin_precipitation_in < 0.05 then 'light precipitation'
            when origin_precipitation_in < 0.2 then 'moderate precipitation'
            else 'heavy precipitation'
        end as precipitation_band,
        case
            when origin_wind_speed_mph is null then 'unknown'
            when origin_wind_speed_mph < 10 then 'wind under 10 mph'
            when origin_wind_speed_mph < 20 then 'wind 10 to 20 mph'
            when origin_wind_speed_mph < 30 then 'wind 20 to 30 mph'
            else 'wind 30 mph or more'
        end as wind_band
    from {{ ref('fct_flight') }}

),

unpivoted as (

    select
        'visibility' as condition_type,
        visibility_band as condition_band,
        *
    from flights

    union all

    select
        'precipitation' as condition_type,
        precipitation_band as condition_band,
        *
    from flights

    union all

    select
        'wind' as condition_type,
        wind_band as condition_band,
        *
    from flights

)

select
    condition_type,
    condition_band,
    count(*) as flight_count,
    count(*) filter (is_cancelled) as cancelled_count,
    count(*) filter (is_departure_delayed) as departure_delayed_count,
    round(100.0 * count(*) filter (is_cancelled) / count(*), 2) as cancellation_rate_pct,
    round(100.0 * count(*) filter (is_departure_delayed) / count(*), 2)
        as departure_delay_rate_pct,
    round(avg(departure_delay_minutes), 2) as avg_departure_delay_minutes,
    round(median(departure_delay_minutes), 2) as median_departure_delay_minutes,
    round(quantile_cont(departure_delay_minutes, 0.9), 2) as p90_departure_delay_minutes
from unpivoted
where condition_band <> 'unknown'
group by condition_type, condition_band
order by condition_type, condition_band
