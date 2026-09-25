select
    region_id,
    extract(dow from local_date)::integer as day_of_week,
    local_hour,
    count(*)::integer as observed_intervals,
    avg(price_aud_per_mwh) as mean_price_aud_per_mwh,
    median(price_aud_per_mwh) as median_price_aud_per_mwh,
    quantile_cont(price_aud_per_mwh, 0.95) as p95_price_aud_per_mwh
from {{ ref('fct_market_price') }}
group by 1, 2, 3
