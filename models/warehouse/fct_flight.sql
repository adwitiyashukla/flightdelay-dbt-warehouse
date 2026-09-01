{{
    config(
        materialized='incremental',
        unique_key='flight_key',
        incremental_strategy='delete+insert'
    )
}}

with flights as (

    select * from {{ ref('stg_flight') }}

    {% if is_incremental() %}
    where flight_date >= (select coalesce(max(flight_date), date '1900-01-01') from {{ this }})
    {% endif %}

),

weather as (

    select * from {{ ref('stg_weather') }}

)

select
    flights.flight_key,
    {{ surrogate_key(['flights.flight_date']) }} as date_key,
    {{ surrogate_key(['flights.carrier_code']) }} as carrier_key,
    {{ surrogate_key(['flights.origin_code']) }} as origin_airport_key,
    {{ surrogate_key(['flights.destination_code']) }} as destination_airport_key,
    {{ surrogate_key(['flights.tail_number']) }} as aircraft_key,
    flights.flight_date,
    flights.carrier_code,
    flights.flight_number,
    flights.tail_number,
    flights.origin_code,
    flights.destination_code,
    flights.origin_code || '-' || flights.destination_code as route_code,
    flights.scheduled_departure_hour_utc,
    flights.scheduled_departure_minute,
    flights.scheduled_arrival_minute,
    flights.actual_departure_minute,
    flights.actual_arrival_minute,
    flights.scheduled_departure_minute // 60 as scheduled_departure_hour_local,
    flights.departure_delay_minutes,
    flights.arrival_delay_minutes,
    flights.air_time_minutes,
    flights.distance_miles,
    flights.is_cancelled,
    flights.is_diverted,
    coalesce(flights.departure_delay_minutes > 15, false) as is_departure_delayed,
    coalesce(flights.arrival_delay_minutes > 15, false) as is_arrival_delayed,
    case
        when flights.arrival_delay_minutes is null or flights.departure_delay_minutes is null
            then null
        else flights.arrival_delay_minutes - flights.departure_delay_minutes
    end as delay_change_in_air_minutes,
    weather.temperature_f as origin_temperature_f,
    weather.wind_speed_mph as origin_wind_speed_mph,
    weather.precipitation_in as origin_precipitation_in,
    weather.visibility_miles as origin_visibility_miles,
    coalesce(weather.precipitation_in > 0, false) as origin_had_precipitation,
    coalesce(weather.visibility_miles < 3, false) as origin_had_low_visibility
from flights
left join weather
    on flights.origin_code = weather.origin_code
    and flights.scheduled_departure_hour_utc = weather.observed_hour_utc
