# Power BI report specification

The BI report remains to be authored in a compatible Power BI environment. Power BI Desktop requires Windows; the project's primary dashboard and reproducible pipeline run on macOS.

`energy-platform export-bi` writes these CSV tables after the dbt build:

- `dim_region.csv`
- `fct_market_price.csv`
- `fct_operational_demand.csv`
- `daily_price_metrics.csv`
- `hourly_price_patterns.csv`
- `dim_date.csv`
- `scenario_daily.csv` (after running `energy-platform evaluate`)

Proposed report pages:

1. Market overview: date and region slicers, daily wholesale price and half-hour demand trends, coverage card.
2. Price risk: median by hour and weekday, negative-price share, 95th-percentile and maximum price.
3. Scenario summary: the **precalculated** `scenario_daily.csv`; label the invented load and wholesale-only interpretation beside the figures.
4. Definitions: links to sources and units, differing price/demand grains, refresh date, and limitations.

Connect `dim_date[local_date]` to `daily_price_metrics[local_date]`, `fct_market_price[local_date]`, `fct_operational_demand[local_date]`, and `scenario_daily[date]` (convert it to Date first). Connect `dim_region[region_id]` to the regional facts. Use one-way filtering from dimensions to facts. Avoid a direct relationship between five-minute prices and half-hour demand. `hourly_price_patterns` is already aggregated across the full loaded period; do not imply date slicers filter it.

Suggested measures:

```dax
Average Wholesale Price (AUD/MWh) = AVERAGE(fct_market_price[price_aud_per_mwh])
Negative Price Share = DIVIDE(CALCULATE(COUNTROWS(fct_market_price), fct_market_price[price_aud_per_mwh] < 0), COUNTROWS(fct_market_price))
Scenario Original (AUD) = SUM(scenario_daily[original_aud])
Scenario Alternative (AUD) = SUM(scenario_daily[alternative_aud])
Scenario Difference (AUD) = SUM(scenario_daily[reduction_aud])
```

Reconcile the unsliced scenario totals to **$291.74 original, $236.43 alternative, and $55.31 difference** across 75 complete firm days. The market-price mean on the report should follow the five-minute fact table rather than an unweighted average of daily means. Add the actual `.pbix` or `.pbit`, screenshots, and model diagram to this folder after authoring and verification.
