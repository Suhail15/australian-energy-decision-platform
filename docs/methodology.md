# Methodology and limits

## Market measures

The primary price series is AEMO's firm `RRP` for Queensland, in AUD/MWh, for each five-minute interval. Daily means are arithmetic means of equal-length intervals, so they are time-weighted averages. The daily maximum preserves five-minute spikes. Half-hour actual operational demand is shown as a separate context series, never forward-filled onto price records.

Data quality checks look for duplicate region/interval keys, missing five-minute observations, missing values, and interval misalignment. A complete Queensland local day has 288 five-minute price intervals and 48 half-hour demand observations. Only the price requirement controls whether a day enters the business scenario comparison.

## Example business scenario

The demonstration profile has a 5 kW background load from 08:00 to 20:00 and a further 5 kW flexible load for two hours. The original flexible window is 16:00–18:00; the alternative is 11:00–13:00. Either schedule uses 70 kWh daily, with a maximum combined load of 10 kW.

For each five-minute interval:

```text
energy_kwh = load_kw × (5 / 60)
wholesale_exposure_aud = energy_kwh × price_aud_per_mwh / 1,000
```

The daily difference is original exposure minus alternative exposure. A positive number means the alternative had lower historical wholesale exposure. A negative number means it performed worse. Negative prices are retained in the calculation.

The default operating windows were specified before inspecting the holdout period. The holdout begins 14 June 2026. Both schedules are compared on the same complete days. A day with any missing or duplicate five-minute price interval is excluded from both schedules and counted in the result.

The primary result uses only prices marked `FIRM` by AEMO. A separate sensitivity result includes `NOT FIRM` observations while keeping the same schedules and interval checks. AEMO marks those prices as subject to review; that sensitivity is not a second set of confirmed prices. The gap between the two results also reveals how much evidence is omitted by the stricter rule.

The scenario is a **historical fixed-schedule comparison**, not a forecast or day-ahead optimisation. It assumes the load can be moved without productivity loss or other operating costs. It contains no actual customer meter data, retail tariff, network charge, tax, hedging arrangement, or contract terms. A wholesale-market difference is not a customer-bill saving.

CER annual facility emissions and renewable-project capacity may be added to a separate context page. Their time and entity grains differ from the five-minute market data; this project does not infer marginal emissions for the load shift.
