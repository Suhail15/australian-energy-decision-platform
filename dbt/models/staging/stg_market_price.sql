select
    region_id,
    interval_start_utc,
    timezone('Australia/Brisbane', interval_start_utc) as interval_start_aest,
    cast(price_aud_per_mwh as double) as price_aud_per_mwh,
    price_status,
    invalid_flag,
    source_file
from {{ source('aemo', 'raw_price') }}
