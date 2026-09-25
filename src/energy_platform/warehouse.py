"""Load immutable prepared observations and run dbt transformations."""

from __future__ import annotations

import os
import json
import subprocess
import sys
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
