{% snapshot snap_airport_reference %}

{{
    config(
        target_schema='snapshots',
        unique_key='ident',
        strategy='check',
        check_cols=['airport_type', 'airport_name', 'municipality', 'has_scheduled_service'],
        invalidate_hard_deletes=True
    )
}}

select
    ident,
    airport_type,
    airport_name,
    municipality,
    iso_country,
    iso_region,
    has_scheduled_service
from {{ ref('stg_airport_reference') }}

{% endsnapshot %}
