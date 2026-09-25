"""Load immutable prepared observations and run dbt transformations."""

from __future__ import annotations

import os
import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from .paths import PROCESSED, ROOT, database_path


def load_raw() -> Path:
    database = database_path()
    database.parent.mkdir(parents=True, exist_ok=True)
    for name in ("price", "demand"):
        if not (PROCESSED / f"{name}.parquet").exists():
            raise FileNotFoundError(f"Prepare {name} observations first")
    with duckdb.connect(str(database)) as con:
        for name in ("price", "demand"):
            source = str(PROCESSED / f"{name}.parquet")
            con.execute(f"CREATE OR REPLACE TABLE raw_{name} AS SELECT * FROM read_parquet(?)", [source])
    return database


def run_dbt() -> None:
    env = os.environ.copy()
    env["ENERGY_DB_PATH"] = str(database_path())
    command = [str(Path(sys.executable).parent / "dbt"), "build", "--project-dir", str(ROOT / "dbt"), "--profiles-dir", str(ROOT / "dbt")]
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def export_bi() -> list[Path]:
    output = ROOT / "data" / "processed" / "bi"
    output.mkdir(parents=True, exist_ok=True)
    tables = ["dim_region", "fct_market_price", "fct_operational_demand", "daily_price_metrics", "hourly_price_patterns"]
    paths = []
    with duckdb.connect(str(database_path()), read_only=True) as con:
        for table in tables:
            path = output / f"{table}.csv"
            con.execute(f"COPY (SELECT * FROM {table}) TO ? (HEADER, DELIMITER ',')", [str(path)])
            paths.append(path)
        bounds = con.execute("SELECT min(local_date), max(local_date) FROM daily_price_metrics").fetchone()
    dates = pd.date_range(bounds[0], bounds[1], freq="D")
    date_dimension = pd.DataFrame({
        "local_date": dates.date,
        "year": dates.year,
        "month_number": dates.month,
        "month_name": dates.strftime("%B"),
        "day_of_week_monday_zero": dates.dayofweek,
        "day_name": dates.strftime("%A"),
    })
    date_path = output / "dim_date.csv"
    date_dimension.to_csv(date_path, index=False)
    paths.append(date_path)
    result = ROOT / "reports" / "holdout_result.json"
    if result.exists():
        daily = pd.DataFrame(json.loads(result.read_text())["daily"])
        scenario_path = output / "scenario_daily.csv"
        daily.to_csv(scenario_path, index=False)
        paths.append(scenario_path)
    return paths


def package_bi() -> list[Path]:
    """Commit-sized, dated Power BI Desktop inputs independent of the local warehouse."""
    exports = {path.name: path for path in export_bi()}
    names = ["dim_date.csv", "dim_region.csv", "daily_price_metrics.csv",
             "hourly_price_patterns.csv", "scenario_daily.csv"]
    missing = [name for name in names if name not in exports]
    if missing:
        raise FileNotFoundError(f"Run energy-platform evaluate before packaging BI data: {missing}")
    output = ROOT / "powerbi" / "data"
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        path = output / name
        shutil.copyfile(exports[name], path)
        paths.append(path)
    demand_path = output / "daily_demand_metrics.csv"
    with duckdb.connect(str(database_path()), read_only=True) as con:
        con.execute("""
            COPY (
                SELECT region_id, local_date, count(*)::integer AS observed_intervals,
                       avg(operational_demand_mw) AS mean_operational_demand_mw,
                       max(operational_demand_mw) AS peak_operational_demand_mw
                FROM fct_operational_demand
                GROUP BY region_id, local_date
                ORDER BY region_id, local_date
            ) TO ? (HEADER, DELIMITER ',')
        """, [str(demand_path)])
        first_date, last_date = con.execute(
            "SELECT min(local_date), max(local_date) FROM daily_price_metrics"
        ).fetchone()
    paths.append(demand_path)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": f"AEMO NEMWeb Queensland observations, {first_date} to {last_date}",
        "scenario": "Hypothetical 5 kW activity shifted 16:00-18:00 to 11:00-13:00; FIRM price holdout only",
        "files": {path.name: {"bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in paths},
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return paths + [manifest_path]
