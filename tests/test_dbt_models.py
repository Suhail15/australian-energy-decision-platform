"""Exercise the real SQL models with a small independently understood source set."""

import os
import subprocess
import sys
from pathlib import Path

import duckdb

from energy_platform.paths import ROOT


def test_dbt_filters_review_pending_prices_and_preserves_demand_grain(tmp_path):
    database = tmp_path / "test.duckdb"
    with duckdb.connect(str(database)) as con:
        con.execute("""
            create table raw_price (
                region_id varchar, interval_start_utc timestamptz,
                price_aud_per_mwh double, price_status varchar,
                invalid_flag varchar, source_file varchar
            )
        """)
        con.execute("""
            insert into raw_price values
            ('QLD1', '2026-08-05 01:00:00+00', -50, 'FIRM', '0', 'fixture.zip'),
            ('QLD1', '2026-08-05 01:05:00+00', 100, 'NOT FIRM', '0', 'fixture.zip')
        """)
        con.execute("""
            create table raw_demand (
                region_id varchar, interval_start_utc timestamptz,
                operational_demand_mw double, demand_adjustment_mw double,
                source_file varchar
            )
        """)
        con.execute("insert into raw_demand values ('QLD1', '2026-08-05 01:00:00+00', 6000, 0, 'fixture.zip')")
    env = os.environ.copy()
    env["ENERGY_DB_PATH"] = str(database)
    dbt = str(Path(sys.executable).parent / "dbt")
    result = subprocess.run(
        [dbt, "build", "--project-dir", str(ROOT / "dbt"), "--profiles-dir", str(ROOT / "dbt"), "--quiet"],
        cwd=ROOT, env=env, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with duckdb.connect(str(database), read_only=True) as con:
        assert con.execute("select count(*) from fct_market_price").fetchone()[0] == 1
        assert con.execute("select price_aud_per_mwh from fct_market_price").fetchone()[0] == -50
        assert con.execute("select interval_start_aest from fct_market_price").fetchone()[0].hour == 11
        assert con.execute("select count(*) from fct_operational_demand").fetchone()[0] == 1
        assert con.execute("select observed_intervals from daily_price_metrics").fetchone()[0] == 1
