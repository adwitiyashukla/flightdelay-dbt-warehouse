select
    ident,
    nullif(trim(type), '') as airport_type,
    nullif(trim(name), '') as airport_name,
    nullif(trim(iso_country), '') as iso_country,
    nullif(trim(iso_region), '') as iso_region,
    nullif(trim(municipality), '') as municipality,
    scheduled_service = 'yes' as has_scheduled_service,
    latitude_deg as latitude,
    longitude_deg as longitude,
    elevation_ft,
    nullif(trim(iata_code), '') as iata_code,
    nullif(trim(local_code), '') as local_code
from {{ source('raw', 'ourairports_airports') }}
