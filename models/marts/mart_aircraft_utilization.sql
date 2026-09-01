with flights as (

    select * from {{ ref('fct_flight') }}

),

aircraft as (

    select * from {{ ref('dim_aircraft') }}

),

aggregated as (

    select
        flights.aircraft_key,
        count(*) as flight_count,
        count(distinct flights.flight_date) as active_day_count,
        count(distinct flights.carrier_code) as carrier_count,
        count(distinct flights.route_code) as route_count,
        sum(flights.air_time_minutes) as total_air_time_minutes,
        sum(flights.distance_miles) as total_distance_miles,
        avg(flights.arrival_delay_minutes) as avg_arrival_delay_minutes
    from flights
    where flights.tail_number is not null
    group by flights.aircraft_key

)

select
    aircraft.tail_number,
    aircraft.manufacturer,
    aircraft.model,
    aircraft.size_class,
    aircraft.seat_count,
    aircraft.manufactured_year,
    aircraft.age_years_in_2013,
    aircraft.has_reference_record,
    aggregated.flight_count,
    aggregated.active_day_count,
    aggregated.carrier_count,
    aggregated.route_count,
    aggregated.total_air_time_minutes,
    aggregated.total_distance_miles,
    round(aggregated.flight_count * 1.0 / nullif(aggregated.active_day_count, 0), 2)
        as flights_per_active_day,
    round(aggregated.avg_arrival_delay_minutes, 2) as avg_arrival_delay_minutes
from aggregated
inner join aircraft
    on aggregated.aircraft_key = aircraft.aircraft_key
order by aggregated.flight_count desc
