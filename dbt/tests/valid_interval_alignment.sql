select region_id, interval_start_utc
from {{ ref('fct_market_price') }}
where extract(minute from interval_start_aest)::integer % 5 != 0
   or extract(second from interval_start_aest) != 0
