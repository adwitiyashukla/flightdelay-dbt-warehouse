with source as (

    select * from {{ source('raw', 'flights') }}

),

renamed as (

    select
        rownames as flight_key,
        make_date(year, month, day) as flight_date,
        carrier as carrier_code,
        flight as flight_number,
        nullif(trim(tailnum), '') as tail_number,
        origin as origin_code,
        dest as destination_code,
        (sched_dep_time // 100 * 60 + sched_dep_time % 100) % 1440 as scheduled_departure_minute,
        (sched_arr_time // 100 * 60 + sched_arr_time % 100) % 1440 as scheduled_arrival_minute,
        case
            when dep_time is null then null
            else (dep_time // 100 * 60 + dep_time % 100) % 1440
        end as actual_departure_minute,
        case
            when arr_time is null then null
            else (arr_time // 100 * 60 + arr_time % 100) % 1440
        end as actual_arrival_minute,
        dep_delay as departure_delay_minutes,
        arr_delay as arrival_delay_minutes,
        air_time as air_time_minutes,
        distance as distance_miles,
        cast(time_hour at time zone 'UTC' as timestamp) as scheduled_departure_hour_utc,
        dep_time is null as is_cancelled,
        dep_time is not null and arr_delay is null as is_diverted

    from source

)

select * from renamed
