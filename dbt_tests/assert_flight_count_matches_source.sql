with source_count as (

    select count(*) as row_count from {{ source('raw', 'flights') }}

),

fact_count as (

    select count(*) as row_count from {{ ref('fct_flight') }}

)

select
    source_count.row_count as source_rows,
    fact_count.row_count as fact_rows
from source_count
cross join fact_count
where source_count.row_count <> fact_count.row_count
