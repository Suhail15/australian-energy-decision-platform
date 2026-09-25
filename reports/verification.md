# Independent result check

The fixed-window difference can be calculated without the Python scenario module. The following DuckDB query was run against `fct_market_price` after the dbt build and returned **75 complete days, $55.31 total exposure reduction, $0.1752 minimum daily difference**. The Python result independently returned 75 days, $55.31, and $0.18 after rounding.

```sql
with daily as (
    select
        local_date,
        count(*) as intervals,
        sum(case when local_hour in (16, 17) then price_aud_per_mwh else 0 end) as original_price_sum,
        sum(case when local_hour in (11, 12) then price_aud_per_mwh else 0 end) as alternative_price_sum
    from fct_market_price
    where local_date between date '2026-06-14' and date '2026-09-12'
    group by local_date
)
select
    count(*) as complete_days,
    round(sum((original_price_sum - alternative_price_sum) * 5 / 12000), 2) as difference_aud,
    min((original_price_sum - alternative_price_sum) * 5 / 12000) as smallest_daily_difference_aud
from daily
where intervals = 288;
```

The factor `5 / 12000` represents a 5 kW flexible load, 12 five-minute intervals per hour, and 1,000 kWh per MWh. Background load cancels because both schedules use the same background profile.

The full local run passed all 22 dbt models and checks and all nine Python tests. The Docker Compose build started both services; the dashboard returned HTTP 200 and the containerized API returned the same coverage figures as the local API. GitHub Actions has not run yet because this repository has not been published.
