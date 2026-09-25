select
    region_id,
    local_date,
    count(*)::integer as observed_intervals,
    avg(price_aud_per_mwh) as mean_price_aud_per_mwh,
    median(price_aud_per_mwh) as median_price_aud_per_mwh,
    quantile_cont(price_aud_per_mwh, 0.05) as p05_price_aud_per_mwh,
    quantile_cont(price_aud_per_mwh, 0.95) as p95_price_aud_per_mwh,
    max(price_aud_per_mwh) as max_price_aud_per_mwh,
    stddev_pop(price_aud_per_mwh) as price_stddev,
    sum(case when price_aud_per_mwh < 0 then 1 else 0 end)::integer as negative_intervals
from {{ ref('fct_market_price') }}
group by 1, 2
