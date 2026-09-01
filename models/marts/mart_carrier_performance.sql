with flights as (

    select * from {{ ref('fct_flight') }}

),

carriers as (

    select * from {{ ref('dim_carrier') }}

),

aggregated as (

    select
        flights.carrier_key,
        count(*) as flight_count,
        count(*) filter (flights.is_cancelled) as cancelled_count,
        count(*) filter (flights.is_diverted) as diverted_count,
        count(*) filter (flights.is_departure_delayed) as departure_delayed_count,
        count(*) filter (flights.is_arrival_delayed) as arrival_delayed_count,
        count(distinct flights.destination_code) as destination_count,
        count(distinct flights.tail_number) as aircraft_count,
        avg(flights.departure_delay_minutes) as avg_departure_delay_minutes,
        avg(flights.arrival_delay_minutes) as avg_arrival_delay_minutes,
        median(flights.arrival_delay_minutes) as median_arrival_delay_minutes,
        quantile_cont(flights.arrival_delay_minutes, 0.9) as p90_arrival_delay_minutes,
        avg(flights.delay_change_in_air_minutes) as avg_delay_change_in_air_minutes,
        sum(flights.distance_miles) as total_distance_miles
    from flights
    group by flights.carrier_key

)

select
    carriers.carrier_code,
    carriers.carrier_name,
    aggregated.flight_count,
    aggregated.cancelled_count,
    aggregated.diverted_count,
    aggregated.departure_delayed_count,
    aggregated.arrival_delayed_count,
    aggregated.destination_count,
    aggregated.aircraft_count,
    round(100.0 * aggregated.cancelled_count / aggregated.flight_count, 2)
        as cancellation_rate_pct,
    round(100.0 * aggregated.departure_delayed_count / aggregated.flight_count, 2)
        as departure_delay_rate_pct,
    round(100.0 * aggregated.arrival_delayed_count / aggregated.flight_count, 2)
        as arrival_delay_rate_pct,
    round(aggregated.avg_departure_delay_minutes, 2) as avg_departure_delay_minutes,
    round(aggregated.avg_arrival_delay_minutes, 2) as avg_arrival_delay_minutes,
    round(aggregated.median_arrival_delay_minutes, 2) as median_arrival_delay_minutes,
    round(aggregated.p90_arrival_delay_minutes, 2) as p90_arrival_delay_minutes,
    round(aggregated.avg_delay_change_in_air_minutes, 2) as avg_delay_change_in_air_minutes,
    aggregated.total_distance_miles
from aggregated
inner join carriers
    on aggregated.carrier_key = carriers.carrier_key
order by aggregated.flight_count desc
