with coverage as (

    select
        count(*) as total_flights,
        count(*) filter (origin_temperature_f is not null) as matched_flights
    from {{ ref('fct_flight') }}

)

select
    total_flights,
    matched_flights,
    round(100.0 * matched_flights / total_flights, 2) as coverage_pct
from coverage
where 100.0 * matched_flights / total_flights < 99.0
