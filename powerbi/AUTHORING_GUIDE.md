# Queensland energy market: Power BI Desktop build guide

Source: `Suhail15/australian-energy-decision-platform`, with the compact handoff in `c74034121399dd52a22d90dac46d5f570146341d` and the Windows line-ending rule in `8eb606b` (checked 27 September 2026). The four-page report is saved at `powerbi/queensland_energy_market.pbix`. It imports the six committed CSVs in `powerbi/data/`; `manifest.json` is a checksum record, not a model table.

## Import and model

1. In Desktop, import all six CSVs with **Get data > Text/CSV**, using **Import** storage. Rename each query after its filename without `.csv`. In Power Query, use explicit types: dates for `dim_date[local_date]`, both daily fact `local_date` fields, and `scenario_daily[date]`; whole numbers for year, month, weekdays, hours, `observed_intervals`, and `negative_intervals`; decimal numbers for all prices, MW values, and AUD values; text for region and name fields. Use a locale that parses ISO dates and dot decimals. Apply changes.
2. Disable Auto date/time for this file and mark `dim_date` as the date table on `local_date`. Its 364 dates are contiguous from 14 September 2025 through 12 September 2026.
3. Create these **active, one-to-many, single-direction** relationships, with filtering from the dimension to the fact:

   | One side | Many side |
   | --- | --- |
   | `dim_date[local_date]` | `daily_price_metrics[local_date]` |
   | `dim_date[local_date]` | `daily_demand_metrics[local_date]` |
   | `dim_date[local_date]` | `scenario_daily[date]` |
   | `dim_region[region_id]` | `daily_price_metrics[region_id]` |
   | `dim_region[region_id]` | `daily_demand_metrics[region_id]` |

4. Leave `hourly_price_patterns` disconnected. It is aggregated across the entire loaded period, so a date slicer cannot filter it. Do not add a region slicer: the snapshot has only `QLD1`, and `scenario_daily` has no region key.
5. Add the measures and hourly calculated column from [queensland_energy_market.dax](queensland_energy_market.dax). The tested [DAX Query View script](create_and_check_measures.dax) adds all measures together with **Update model with changes** and returns reconciliation values. In `hourly_price_patterns`, sort `Day Name` by `day_of_week` (Sunday=0); sort `dim_date[day_name]` by `day_of_week_monday_zero` (Monday=0). The two weekday codes have different conventions and must not be related.
6. Display dates and times as **Queensland AEST (UTC+10)**. Price units are **AUD/MWh**, operational demand is **MW**, and scenario exposure is **AUD**. Format currency only at display time; do not round imported values or sum displayed rounded daily amounts.

## Page-by-page visual specification

| Page | Visuals and fields | Filters, interactions, and labels |
| --- | --- | --- |
| **1. Market overview** | Between-style slicer on `dim_date[local_date]`; line chart of `Weighted Mean Price (AUD/MWh)` by local date; separate line chart of `Mean Operational Demand (MW)` by local date; cards for `Price Intervals`, `Complete Firm Price Days`, and `Negative Price Share`. | Default full snapshot. Both lines use the same date slicer. Separate axes keep AUD/MWh and MW clear. Daily price line uses observed-interval weighting; do not average daily means in a card. Subtitle: “Queensland AEST; AEMO FIRM five-minute price and half-hour operational demand.” |
| **2. Price risk** | Date slicer; daily line or columns for `Daily P95 Price (AUD/MWh)`; daily maximum line or columns for `Maximum Five-Minute Price (AUD/MWh)`; daily `Negative Price Share`; matrix with `hourly_price_patterns[Day Name]` as rows, `local_hour` as columns, and `Hourly Median Price (AUD/MWh)` as colour-scaled values. | Label P95 explicitly **daily P95**. Never show an average of daily P95 values as a period P95. Give the matrix a permanent title: “Full snapshot median by weekday and hour, 14 Sep 2025–12 Sep 2026; ignores date slicer.” Configure slicer interaction with matrix to **None**. Show hours as 00–23 AEST. |
| **3. Hypothetical schedule** | Date slicer on `dim_date[local_date]`, initially set to 14 Jun–12 Sep 2026; cards for `Scenario Original (AUD)`, `Scenario Alternative (AUD)`, `Scenario Difference (AUD)`, `Scenario Difference (%)`, `Scenario Days`, `Excluded Holdout Days`, and `Scenario Days Better`; daily columns of `Scenario Difference (AUD)` and paired daily lines of original/alternative exposure. | Headline for the full holdout: **$291.74 original; $236.43 alternative; $55.31 difference (18.96%)** across **75 included and 16 excluded days**. Show “5 kW activity, 16:00–18:00 moved to 11:00–13:00; both schedules 70 kWh/day.” Label every monetary visual “historical wholesale exposure for a hypothetical load; not retail-bill savings.” If the date slicer changes, cards represent the selected dates and excluded days within the selected holdout dates. |
| **4. Definitions and quality** | Text boxes or a small table for source, coverage, refresh stamp, grains, completeness rule, assumptions, and exclusions. Optional cards for `Complete Firm Price Days`, `Incomplete Firm Price Days`, and `Peak Operational Demand (MW)`. | State the snapshot was generated 25 Sep 2026 UTC and is not live. Price: AEMO Queensland FIRM RRP every five minutes; complete day = 288 observations. Demand: half-hour regional operational demand; complete day = 48. Scenario: complete FIRM price days only, 14 Jun–12 Sep 2026. Note 16 excluded holdout dates, no meter profile, retail tariff, network charges, tax, hedge, or operating costs. Link to the repository methodology, source audit, and holdout JSON. |

## Saved report status (27 September 2026)

The saved `.pbix` is a readable Power BI package containing a DataModel and four report pages: Market Overview, Price risk, Scenario, and Definitions. Desktop displayed the five intended active relationships, all six tables, and the 21 measures added with `create_and_check_measures.dax`. Its DAX check returned 99,463 price intervals, 225 complete FIRM price days, $291.74 original, $236.43 alternative, $55.31 difference, 75 scenario days, and 16 excluded holdout days. The Scenario cards also displayed 18.96%. The source checker independently passed the manifest, keys, and holdout totals.

The saved pages contain the three overview cards and two daily lines; three price-risk lines and an hourly weekday/hour matrix; six Scenario cards and a daily difference column chart; and two Definitions text boxes. The matrix labels its full-snapshot scope. The saved Scenario page does **not** yet contain the date slicer, `Scenario Days Better` card, or paired original/alternative daily lines in the specification above. The matrix is not yet colour-scaled. A close-and-reopen check and final visual review are pending. These are report-completion tasks, not missing data inputs.

## Reconciliation in Desktop

Use the **full 14 June–12 September 2026 holdout** and clear visual selections before checking the Scenario page.

- [x] Six tables appear. Model view showed exactly the five active relationships above, with no relationship to `hourly_price_patterns`.
- [x] `dim_date` has 364 unique, contiguous dates; daily price and demand each have 364 rows; hourly patterns has 168 rows; `scenario_daily` has 75 rows; region has one `QLD1` row. These counts were checked against the CSVs.
- [x] Market overview full snapshot: `Price Intervals` = **99,463**; `Complete Firm Price Days` = **225**; `Incomplete Firm Price Days` = **139**. Demand has 48 observations on each of 364 dates. The 168 hourly cells also sum to 99,463 observations. The first two measures were checked in Desktop; other counts were checked against the CSVs.
- [x] Scenario full holdout: original **$291.74**, alternative **$236.43**, difference **$55.31**, difference percent **18.96%**, `Holdout Days in Selection` **91**, `Scenario Days` **75**, `Excluded Holdout Days` **16**, `Scenario Days Better` **75**. The six displayed cards and DAX check confirmed the main totals; the non-card values were checked from the model/data.
- [x] Unrounded CSV sums are **291.737715**, **236.432281**, and **55.305432** AUD respectively. The measure `Scenario Difference` computes original minus alternative = **55.305434** AUD. The **$0.000002** difference from the summed `reduction_aud` column is row-level six-decimal rounding and disappears at cent display precision. Do not sum row values after rounding each row to cents.
- [ ] The smallest daily source difference is **$0.175204** on 26 Aug 2026, shown as **$0.18**. Compare a few daily rows against `reports/holdout_result.json` and check the excluded-date list has 16 entries.
- [ ] Move the scenario date slicer to a subset, then confirm all scenario cards and charts follow it. Confirm the full-period hourly matrix remains unchanged when the market/risk date slicer moves. Confirm no visual implies the regional demand series is the hypothetical business load.
- [ ] Save the `.pbix`, close and reopen it in Desktop, repeat the full-holdout card checks, then commit the artifact with a screenshot or note of the verified values. A file existing on disk alone does not verify the report.

## Findings and missing inputs

- **Windows checkout checksum issue and fix:** `manifest.json` hashes the LF bytes in the Git blobs. The initial Windows checkout used `core.autocrlf=true`, producing CRLF files whose physical byte counts and hashes differed. Commit `8eb606b` added `.gitattributes` with `text eol=lf` for these files. Existing checkouts may retain CRLF until the files are refreshed; the companion PowerShell checker validates LF-normalised content in either case. After LF refresh here, the physical files matched the manifest. CSV values are unaffected by line endings.
- **Different weekday numbering:** `dim_date[day_of_week_monday_zero]` uses Monday=0, while `hourly_price_patterns[day_of_week]` uses Sunday=0. Use the calculated label and sort specified above.
- **Aggregated snapshot limits:** The compact files cannot independently reconstruct an overall five-minute price percentile, individual five-minute spikes, or the scenario from raw intervals. The large fact exports and AEMO source files are excluded from Git. The committed `reports/verification.md` records an independent SQL calculation, but the `.pbix` should be reconciled against the committed scenario CSV and JSON.
- **Sensitivity is outside the six-table model:** `reports/holdout_sensitivity.json` documents the provisional `NOT FIRM` comparison, but its daily rows are not among the Power BI CSVs. Add a clearly labelled seventh input only if that sensitivity is to appear in the report; otherwise keep the four pages focused on the FIRM result.
- **Still needed:** Finish the Scenario interactions and optional visuals listed in the saved-report status above; close and reopen the `.pbix` in Desktop; then perform a final visual review. A real customer meter profile, tariff/contract, and operating constraints are absent, so no retail-bill saving can be claimed.
