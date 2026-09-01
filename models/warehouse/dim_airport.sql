with airports as (

    select * from {{ ref('stg_airport') }}

),

usage as (

    select
        destination_code as airport_code,
        count(*) as arriving_flight_count
    from {{ ref('stg_flight') }}
    group by 1

    union all

    select
        origin_code as airport_code,
        count(*) as departing_flight_count
    from {{ ref('stg_flight') }}
    group by 1

),

totals as (

    select
        airport_code,
        sum(arriving_flight_count) as flight_count
    from usage
    group by 1

)

select
    {{ surrogate_key(['airports.airport_code']) }} as airport_key,
    airports.airport_code,
    airports.airport_name,
    airports.municipality,
    airports.iso_country,
    airports.iso_region,
    airports.airport_type,
    airports.latitude,
    airports.longitude,
    airports.elevation_ft,
    airports.time_zone,
    airports.utc_offset_hours,
    coalesce(airports.has_scheduled_service, false) as has_scheduled_service,
    airports.source_system,
    airports.airport_code in ('EWR', 'JFK', 'LGA') as is_nyc_origin,
    coalesce(totals.flight_count, 0) as flight_count_2013
from airports
left join totals
    on airports.airport_code = totals.airport_code
