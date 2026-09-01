select
    flight_key,
    actual_departure_minute,
    arrival_delay_minutes
from {{ ref('fct_flight') }}
where is_cancelled
    and (actual_departure_minute is not null or arrival_delay_minutes is not null)
