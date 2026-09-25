# Power BI Desktop handoff

The six small CSV files in [`data/`](data/) are a public, reproducible snapshot for building the report on Windows. They contain aggregated AEMO market data and the **hypothetical** scenario result. No receipt, customer, or business meter data is included. The actual Power BI report has not yet been authored; add a verified `.pbix` or `.pbit` here after creating it on Windows.

Power BI Desktop [requires Windows](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop). Its browser service [requires a work or school account](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-self-service-sign-up-help), which is not available for this project. The report can be authored and saved locally in Desktop on the user's Windows laptop.

## Open the report data on Windows

1. Install [Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop) and clone this repository.
2. Use **Home → Get data → Text/CSV** to import every CSV in `powerbi/data/`. Name each table after its filename without `.csv`.
3. In Power Query, set `local_date` and `scenario_daily[date]` to **Date**, hour and count fields to **Whole number**, and price, demand, and AUD fields to **Decimal number**. Keep the timezone as Queensland AEST in visual labels.
4. In Model view, create one-to-many, single-direction relationships from `dim_date[local_date]` to `daily_price_metrics[local_date]`, `daily_demand_metrics[local_date]`, and `scenario_daily[date]`. Connect `dim_region[region_id]` to the price and demand daily tables. Keep `hourly_price_patterns` separate because it is pre-aggregated over the whole loaded year; a date slicer must not appear to filter it.
5. Save the report as `powerbi/queensland_energy_market.pbix` in the cloned repository and verify the measures below before committing it.

The snapshot files are:

| Table | Grain | Use |
| --- | --- | --- |
| `dim_date` | one Queensland local date | Date slicer and calendar labels |
| `dim_region` | one region | Queensland label |
| `daily_price_metrics` | region and date | Daily wholesale price, risk, completeness |
| `daily_demand_metrics` | region and date | Daily operational demand context |
| `hourly_price_patterns` | region, weekday, hour across the full year | Weekday/hour price heatmap; Sunday is 0 |
| `scenario_daily` | complete firm-price holdout date | Paired hypothetical wholesale exposure |

The full five-minute price and half-hour demand facts stay out of Git to keep the repository small. On a machine with Python and the AEMO source files, `energy-platform export-bi` creates those larger CSVs in `data/processed/bi/`. `energy-platform package-bi` regenerates the committed compact snapshot from the validated local warehouse and writes a checksum manifest.

## Suggested report

**Market overview:** Date slicer, daily mean wholesale price line, daily mean operational demand line, observed-price interval count, and complete-firm-day count. Label prices `AUD/MWh` and demand `MW`.

**Price risk:** Daily 95th percentile, maximum five-minute price, negative-price share, and the full-year median by weekday and hour. Do not present the average of daily 95th percentiles as an overall 95th percentile. Label the hourly heatmap as full-period because it is not connected to the date dimension.

**Scenario:** Cards for original, alternative, and difference in wholesale exposure; a daily difference chart; the 75 included and 16 excluded holdout days; the 70 kWh/day invented load. Put “historical wholesale exposure for a hypothetical load; not retail-bill savings” beside the headline result.

**Definitions:** AEMO source links, units, five-minute price versus half-hour demand source grains, `FIRM` filtering, holdout dates, and the absence of a real tariff or customer meter profile.

Useful DAX measures for the compact tables:

```dax
Price Intervals = SUM(daily_price_metrics[observed_intervals])

Weighted Mean Price (AUD/MWh) =
DIVIDE(
    SUMX(daily_price_metrics, daily_price_metrics[mean_price_aud_per_mwh] * daily_price_metrics[observed_intervals]),
    [Price Intervals]
)

Negative Price Share =
DIVIDE(SUM(daily_price_metrics[negative_intervals]), [Price Intervals])

Complete Firm Days =
CALCULATE(COUNTROWS(daily_price_metrics), daily_price_metrics[observed_intervals] = 288)

Scenario Original (AUD) = SUM(scenario_daily[original_aud])
Scenario Alternative (AUD) = SUM(scenario_daily[alternative_aud])
Scenario Difference (AUD) = SUM(scenario_daily[reduction_aud])
Scenario Days = COUNTROWS(scenario_daily)
```

With no slicer applied, the scenario page must show **$291.74 original, $236.43 alternative, $55.31 difference, and 75 complete firm days**. The date dimension spans 14 September 2025–12 September 2026. Compare the report to [`reports/holdout_result.json`](../reports/holdout_result.json) and [`reports/verification.md`](../reports/verification.md) before calling the Power BI artifact complete.
