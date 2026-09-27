# A second check on the result

I wanted a check that did not simply call the same Python scenario function twice. The following DuckDB query reads the modelled five-minute prices directly. It returned **75 complete days, a $55.31 total exposure difference, and a $0.1752 smallest daily difference**. The Python scenario independently returned 75 days, $55.31, and $0.18 after rounding.

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

The full local run passed all 22 dbt models and checks and all nine Python tests. The Docker Compose build started both services; the dashboard returned HTTP 200 and the containerized API returned the same coverage figures as the local API. [GitHub Actions](../.github/workflows/checks.yml) runs the offline Python checks on pushes and pull requests. A live AEMO download is intentionally separate because the upstream files and network can change.
