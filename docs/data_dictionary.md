# Data dictionary

The tables intentionally have different grains. Five-minute prices drive the scenario; half-hour regional demand is context. I keep those separate so a chart cannot quietly turn regional demand into the invented business's consumption.

| Table | Grain | Main fields | Notes |
| --- | --- | --- | --- |
| `raw_price` | One extracted Queensland trading-price record | `interval_start_utc`, `price_aud_per_mwh`, `price_status`, `invalid_flag`, `source_file` | Original source values are in local excluded Parquet and source ZIP files. |
| `raw_demand` | One extracted Queensland operational-demand record | `interval_start_utc`, `operational_demand_mw`, `demand_adjustment_mw`, `source_file` | Published half-hour readings. |
| `fct_market_price` | One valid firm price per Queensland five-minute interval | `interval_start_utc`, `interval_start_aest`, `local_date`, `price_aud_per_mwh` | Used for scenario exposure. |
| `fct_operational_demand` | One half-hour demand reading | `interval_start_utc`, `interval_start_aest`, `operational_demand_mw` | Regional context; separate from example business use. |
| `daily_price_metrics` | One Queensland local day | observed count, mean, median, percentiles, max, standard deviation, negative count | Complete day has 288 observations. |
| `hourly_price_patterns` | One weekday/hour combination over the loaded period | observed count, mean, median, 95th percentile | Sunday is 0. |
| `daily_demand_metrics` (Power BI snapshot) | One Queensland local day | observed half-hour count, mean and peak operational demand in MW | Derived from `fct_operational_demand`; regional context only. |
| `scenario_daily` (Power BI snapshot) | One complete firm-price holdout day | original, alternative, difference in AUD | Hypothetical wholesale exposure, not retail-bill savings. |

`MW` is power at an instant or averaged interval. `MWh` and `kWh` are energy over time. The scenario converts power in kW to energy in kWh using the five-minute interval duration, then divides by 1,000 because prices are per MWh.
