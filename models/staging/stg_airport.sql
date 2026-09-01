with nyc_airports as (

    select
        faa as airport_code,
        nullif(trim(name), '') as airport_name,
        lat as latitude,
        lon as longitude,
        alt as elevation_ft,
        tz as utc_offset_hours,
        nullif(trim(tzone), '') as time_zone
    from {{ source('raw', 'airports') }}

),

reference as (

    select * from {{ ref('stg_airport_reference') }}

),

by_iata as (

    select *
    from reference
    where iata_code is not null

),

by_local as (

    select
        *,
        row_number() over (partition by local_code order by ident) as local_rank
    from reference
    where local_code is not null and iata_code is null

),

matched as (

    select
        nyc_airports.airport_code,
        nyc_airports.airport_name,
        nyc_airports.latitude,
        nyc_airports.longitude,
        nyc_airports.elevation_ft,
        nyc_airports.utc_offset_hours,
        nyc_airports.time_zone,
        coalesce(by_iata.airport_type, by_local.airport_type) as airport_type,
        coalesce(by_iata.iso_country, by_local.iso_country) as iso_country,
        coalesce(by_iata.iso_region, by_local.iso_region) as iso_region,
        coalesce(by_iata.municipality, by_local.municipality) as municipality,
        coalesce(by_iata.has_scheduled_service, by_local.has_scheduled_service)
            as has_scheduled_service,
        case
            when by_iata.ident is not null then 'faa_matched_iata'
            when by_local.ident is not null then 'faa_matched_local'
            else 'faa_only'
        end as source_system
    from nyc_airports
    left join by_iata
        on nyc_airports.airport_code = by_iata.iata_code
    left join by_local
        on nyc_airports.airport_code = by_local.local_code
        and by_local.local_rank = 1

),

flight_endpoints as (

    select distinct origin_code as airport_code from {{ ref('stg_flight') }}
    union
    select distinct destination_code as airport_code from {{ ref('stg_flight') }}

),

gap_filled as (

    select
        flight_endpoints.airport_code,
        by_iata.airport_name,
        by_iata.latitude,
        by_iata.longitude,
        by_iata.elevation_ft,
        cast(null as bigint) as utc_offset_hours,
        cast(null as varchar) as time_zone,
        by_iata.airport_type,
        by_iata.iso_country,
        by_iata.iso_region,
        by_iata.municipality,
        by_iata.has_scheduled_service,
        'reference_only' as source_system
    from flight_endpoints
    inner join by_iata
        on flight_endpoints.airport_code = by_iata.iata_code
    where flight_endpoints.airport_code not in (select airport_code from matched)

)

select * from matched
union all
select * from gap_filled
