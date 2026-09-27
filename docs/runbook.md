# Running it again

The repository includes a small Power BI snapshot, so you can open the report without rebuilding the warehouse. For a full rebuild, install the Python package as shown in the [README](../README.md), then run these commands from the repository root:

```bash
energy-platform sync
energy-platform prepare
energy-platform build
energy-platform evaluate
energy-platform export-bi
energy-platform package-bi
```

`sync` caches the AEMO ZIP files and writes their URLs, retrieval times, sizes, and hashes to a local manifest. `prepare` refuses a source file whose hash no longer matches. `build` replaces the local raw warehouse tables, runs dbt models, and checks their keys and interval alignment. The dashboard and API read that warehouse; they do not download data when someone opens a page.

If a download fails, rerun `sync`. If AEMO changes a report format, inspect the source file and update the [source audit](source_audit.md) before changing the parser. For a dbt failure, run `dbt debug --project-dir dbt --profiles-dir dbt` with `ENERGY_DB_PATH` set to the local database path. If a day looks incomplete, check the source manifest and `daily_price_metrics.observed_intervals`; the scenario does not fill missing prices.

Run `python -m pytest -q` for the offline parser and calculation tests. Only run `export-bi` after a successful build. After `evaluate`, `package-bi` refreshes the six tracked Power BI CSVs and their checksum manifest. Recheck the [holdout totals](../reports/holdout_result.json) and commit the CSVs and manifest together.
