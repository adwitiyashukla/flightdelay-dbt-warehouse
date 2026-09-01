with flown as (

    select distinct tail_number
    from {{ ref('stg_flight') }}
    where tail_number is not null

),

planes as (

    select * from {{ ref('stg_plane') }}

)

select
    {{ surrogate_key(['flown.tail_number']) }} as aircraft_key,
    flown.tail_number,
    planes.manufacturer,
    planes.model,
    planes.airframe_type,
    planes.engine_type,
    planes.engine_count,
    planes.seat_count,
    planes.manufactured_year,
    case
        when planes.manufactured_year is null then null
        else 2013 - planes.manufactured_year
    end as age_years_in_2013,
    case
        when planes.seat_count is null then 'unknown'
        when planes.seat_count < 100 then 'regional'
        when planes.seat_count < 200 then 'narrowbody'
        else 'widebody'
    end as size_class,
    planes.tail_number is not null as has_reference_record
from flown
left join planes
    on flown.tail_number = planes.tail_number
