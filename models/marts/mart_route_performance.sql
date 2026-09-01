with flights as (

    select * from {{ ref('fct_flight') }}

),

airports as (

    select * from {{ ref('dim_airport') }}

),

aggregated as (

    select
        flights.route_code,
        flights.origin_code,
        flights.destination_code,
        flights.origin_airport_key,
        flights.destination_airport_key,
        count(*) as flight_count,
        count(distinct flights.carrier_code) as carrier_count,
        count(*) filter (flights.is_cancelled) as cancelled_count,
        count(*) filter (flights.is_arrival_delayed) as arrival_delayed_count,
        avg(flights.arrival_delay_minutes) as avg_arrival_delay_minutes,
        avg(flights.air_time_minutes) as avg_air_time_minutes,
        min(flights.distance_miles) as distance_miles
    from flights
    group by
        flights.route_code,
        flights.origin_code,
        flights.destination_code,
        flights.origin_airport_key,
        flights.destination_airport_key

)

select
    aggregated.route_code,
    aggregated.origin_code,
    aggregated.destination_code,
    destination.airport_name as destination_name,
    destination.municipality as destination_city,
    destination.iso_region as destination_region,
    aggregated.distance_miles,
    aggregated.flight_count,
    aggregated.carrier_count,
    aggregated.cancelled_count,
    aggregated.arrival_delayed_count,
    round(100.0 * aggregated.cancelled_count / aggregated.flight_count, 2)
        as cancellation_rate_pct,
    round(100.0 * aggregated.arrival_delayed_count / aggregated.flight_count, 2)
        as arrival_delay_rate_pct,
    round(aggregated.avg_arrival_delay_minutes, 2) as avg_arrival_delay_minutes,
    round(aggregated.avg_air_time_minutes, 2) as avg_air_time_minutes,
    round(aggregated.distance_miles / nullif(aggregated.avg_air_time_minutes, 0) * 60, 1)
        as avg_ground_speed_mph
from aggregated
inner join airports as destination
    on aggregated.destination_airport_key = destination.airport_key
order by aggregated.flight_count desc
