# Power BI Desktop handoff

The six small CSV files in [`data/`](data/) are a public, reproducible snapshot for the locally authored [`queensland_energy_market.pbix`](queensland_energy_market.pbix). They contain aggregated AEMO market data and the **hypothetical** scenario result. No receipt, customer, or business meter data is included. The four-page report was saved, reopened, and reconciled in Power BI Desktop on Windows.

For the complete six-table model, page layouts, and Desktop reconciliation checklist, use [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md). The measures are documented in [`queensland_energy_market.dax`](queensland_energy_market.dax); [`create_and_check_measures.dax`](create_and_check_measures.dax) is the DAX Query View script used to add and check them. On Windows, run `./powerbi/verify_powerbi_inputs.ps1 -RepoPath .` from the repository root to check the manifest, table keys, and holdout CSV against the committed JSON.

Power BI Desktop [requires Windows](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop). Open the committed `.pbix` locally in Desktop to inspect or finish it.

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

The canonical DAX definitions are in [`queensland_energy_market.dax`](queensland_energy_market.dax). The tested [`create_and_check_measures.dax`](create_and_check_measures.dax) adds all 21 measures through DAX Query View and returns the principal reconciliation values. In particular, `Scenario Difference (AUD)` subtracts the alternative exposure from the original exposure; it does not sum `reduction_aud`, which differs by $0.000002 before display rounding.

With the Scenario slicer at 14 June–12 September 2026, the reopened report shows **$291.74 original, $236.43 alternative, $55.31 difference (18.96%), 75 complete FIRM days, and 16 excluded days**. The date dimension spans 14 September 2025–12 September 2026. See [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md) for the full reconciliation checklist and remaining data limitations.
