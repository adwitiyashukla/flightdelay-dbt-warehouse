select
    {{ surrogate_key(['carrier_code']) }} as carrier_key,
    carrier_code,
    carrier_name,
    icao_code,
    callsign,
    country,
    is_active_in_openflights
from {{ ref('stg_carrier') }}
