with source as (

    select * from {{ source('raw', 'weather') }}

),

renamed as (

    select
        origin as origin_code,
        cast(time_hour at time zone 'UTC' as timestamp) as observed_hour_utc,
        temp as temperature_f,
        dewp as dew_point_f,
        humid as relative_humidity_pct,
        wind_dir as wind_direction_deg,
        case when wind_speed > 200 then null else wind_speed end as wind_speed_mph,
        case when wind_gust > 200 then null else wind_gust end as wind_gust_mph,
        precip as precipitation_in,
        pressure as sea_level_pressure_mb,
        visib as visibility_miles

    from source

),

deduplicated as (

    select
        *,
        row_number() over (
            partition by origin_code, observed_hour_utc
            order by temperature_f
        ) as observation_rank
    from renamed

)

select
    origin_code,
    observed_hour_utc,
    temperature_f,
    dew_point_f,
    relative_humidity_pct,
    wind_direction_deg,
    wind_speed_mph,
    wind_gust_mph,
    precipitation_in,
    sea_level_pressure_mb,
    visibility_miles
from deduplicated
where observation_rank = 1
