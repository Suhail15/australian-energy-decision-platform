# Local runbook

Run `energy-platform sync`, `prepare`, then `build` from the repository root. `sync` may reuse existing ZIPs but writes a fresh source manifest with their checksums. `prepare` will fail if a source file no longer matches that manifest. `build` replaces raw warehouse tables and runs dbt models and tests. The dashboard and API read the prepared warehouse and do not download data when a page is requested.

If a download fails, rerun `sync`. A missing or changed AEMO report format requires inspecting the actual file and updating `docs/source_audit.md` before changing the parser. If dbt fails, inspect its error and run `dbt debug --project-dir dbt --profiles-dir dbt` with `ENERGY_DB_PATH` set to the local database path. For incomplete days, inspect the source manifest and `daily_price_metrics.observed_intervals`; no missing price is filled for scenario calculations.

Run `python -m pytest -q` for offline calculation and parser tests. Run `energy-platform export-bi` only after a successful `build` to create the full BI tables in `data/processed/bi/`. After `evaluate`, run `energy-platform package-bi` to refresh the compact, tracked Power BI Desktop inputs in `powerbi/data/`. Check the scenario totals and commit the changed CSVs and checksum manifest together.
