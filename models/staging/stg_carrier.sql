with nyc_airlines as (

    select
        carrier as carrier_code,
        nullif(trim(name), '') as carrier_name
    from {{ source('raw', 'airlines') }}

),

openflights as (

    select
        iata as carrier_code,
        nullif(trim(name), '') as openflights_name,
        nullif(trim(icao), '') as icao_code,
        nullif(trim(callsign), '') as callsign,
        nullif(trim(country), '') as country,
        active = 'Y' as is_active
    from {{ source('raw', 'openflights_airlines') }}
    where iata is not null and active = 'Y'

),

ranked as (

    select
        *,
        row_number() over (partition by carrier_code order by openflights_name) as match_rank
    from openflights

)

select
    nyc_airlines.carrier_code,
    nyc_airlines.carrier_name,
    ranked.icao_code,
    ranked.callsign,
    ranked.country,
    coalesce(ranked.is_active, false) as is_active_in_openflights
from nyc_airlines
left join ranked
    on nyc_airlines.carrier_code = ranked.carrier_code
    and ranked.match_rank = 1
