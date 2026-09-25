select
    region_id,
    interval_start_utc,
    interval_start_aest,
    interval_start_utc + interval '5 minutes' as interval_end_utc,
    cast(interval_start_aest as date) as local_date,
    extract(hour from interval_start_aest)::integer as local_hour,
    price_aud_per_mwh,
    source_file
from {{ ref('stg_market_price') }}
where price_status = 'FIRM' and invalid_flag = '0'
