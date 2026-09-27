# What I actually downloaded

I checked the downloaded AEMO NEMWeb files on 26 September 2026 before building the pipeline. The project uses the National Electricity Market region `QLD1`, which follows Australian Eastern Standard Time (UTC+10) throughout the year. The table below records the exact report families and fields used so the analysis can be traced back to source, rather than inferred from a dashboard label.

| Series | Actual source | Observed fields | Meaning | Interval |
| --- | --- | --- | --- | --- |
| Price | `TradingIS_Reports` weekly ZIP, nested `TRADING.PRICE` records | `SETTLEMENTDATE`, `REGIONID`, `RRP`, `INVALIDFLAG`, `PRICE_STATUS` | Queensland regional reference price; `RRP` in AUD/MWh | 5 minutes |
| Demand | `Operational_Demand/ACTUAL_DAILY` monthly and current daily ZIP, nested `OPERATIONAL_DEMAND.ACTUAL` records | `REGIONID`, `INTERVAL_DATETIME`, `OPERATIONAL_DEMAND`, `OPERATIONAL_DEMAND_ADJUSTMENT` | Queensland actual operational demand in MW | 30 minutes |

`SETTLEMENTDATE` and `INTERVAL_DATETIME` label the **end** of their intervals. The importer subtracts five or thirty minutes to obtain local interval starts, then stores UTC. This distinction matters at midnight.

The price mart selects records with `PRICE_STATUS = 'FIRM'` and `INVALIDFLAG = '0'`. AEMO's [dispatch procedure](https://www.aemo.com.au/-/media/Files/Electricity/NEM/5MS/Procedures-Workstream/Stakeholder-Consultation/Dispatch-Procedures/SO_OP_3705---Dispatch---clean.pdf) says `NOT FIRM` indicates that prices are subject to review. Those records remain in the prepared raw table for a separate sensitivity calculation, clearly labelled as including prices that may be revised. Negative prices and large positive spikes remain. The source also includes other regions and ancillary-service fields; this project selects `QLD1` and `RRP` only.

The source archive is published as report files, rather than a stable REST endpoint. The importer discovers actual ZIP links from AEMO's directory listing, downloads each selected file, and records its address, retrieval timestamp, size, and SHA-256 checksum. Reprocessing checks the hash. Cached files remain stable until an explicit `sync --refresh`. No original AEMO file is committed to Git.

The initial file inspection used the week `PUBLIC_TRADINGIS_20260802_20260808.zip` and the monthly demand file `PUBLIC_ACTUAL_OPERATIONAL_DEMAND_DAILY_20260701.zip`. The former contains 2,016 five-minute report members for seven days. The latter contains nested daily reports with half-hour readings.

For 14 September 2025–12 September 2026 (364 local days), the processed table has 104,814 unique price intervals of 104,832 expected, a gap of 18. Of the available intervals, 99,463 are `FIRM` and 5,351 are `NOT FIRM`. Exactly 225 days contain 288 firm price intervals. The demand table has 17,472 unique half-hour intervals, or 48 on each of the 364 days. The price analysis never fills gaps or silently treats `NOT FIRM` prices as confirmed.

Official descriptions: [AEMO Dispatch/Trading](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-management-system-mms-data/dispatch) and [Operational Demand](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/operational-demand-data).
