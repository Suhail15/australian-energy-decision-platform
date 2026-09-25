"""Read-only access to validated dbt models."""

from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd

from .paths import database_path


def _query(sql: str, params: list | None = None) -> pd.DataFrame:
    with duckdb.connect(str(database_path()), read_only=True) as con:
        return con.execute(sql, params or []).fetchdf()


def coverage() -> dict:
    frame = _query("""
        select min(local_date) as first_date, max(local_date) as last_date,
               count(*) as price_intervals,
               count(distinct local_date) as days,
               sum(case when price_aud_per_mwh < 0 then 1 else 0 end) as negative_price_intervals,
               (select count(*) from daily_price_metrics where observed_intervals = 288) as complete_firm_days,
               (select count(*) from raw_price where price_status = 'NOT FIRM') as not_firm_intervals,
               (select count(*) from raw_price) as available_price_intervals
        from fct_market_price
    """)
    row = frame.iloc[0].to_dict()
    return {key: (value.date().isoformat() if hasattr(value, "date") else int(value) if value is not None else None)
            for key, value in row.items()}


def daily_prices(start: date, end: date) -> pd.DataFrame:
    return _query("""
        select local_date, observed_intervals, mean_price_aud_per_mwh,
               median_price_aud_per_mwh, p05_price_aud_per_mwh,
               p95_price_aud_per_mwh, max_price_aud_per_mwh,
               price_stddev, negative_intervals
        from daily_price_metrics where local_date between ? and ? order by local_date
    """, [start, end])


def hourly_patterns() -> pd.DataFrame:
    return _query("select * from hourly_price_patterns order by day_of_week, local_hour")


def prices_for_scenario(start: date, end: date, include_not_firm: bool = False) -> pd.DataFrame:
    if include_not_firm:
        return _query("""
            select timezone('Australia/Brisbane', interval_start_utc) as interval_start_aest,
                   price_aud_per_mwh from raw_price
            where invalid_flag = '0'
              and cast(timezone('Australia/Brisbane', interval_start_utc) as date) between ? and ?
            order by interval_start_aest
        """, [start, end])
    return _query("""
        select interval_start_aest, price_aud_per_mwh from fct_market_price
        where local_date between ? and ? order by interval_start_aest
    """, [start, end])


def demand_daily(start: date, end: date) -> pd.DataFrame:
    return _query("""
        select local_date, count(*) as observed_intervals,
               avg(operational_demand_mw) as mean_operational_demand_mw,
               max(operational_demand_mw) as peak_operational_demand_mw
        from fct_operational_demand where local_date between ? and ?
        group by local_date order by local_date
    """, [start, end])
