with source as (

    select * from {{ source('raw', 'planes') }}

),

renamed as (

    select
        tailnum as tail_number,
        year as manufactured_year,
        nullif(trim("type"), '') as airframe_type,
        nullif(trim(manufacturer), '') as manufacturer,
        nullif(trim(model), '') as model,
        engines as engine_count,
        seats as seat_count,
        nullif(trim(engine), '') as engine_type

    from source

)

select * from renamed
