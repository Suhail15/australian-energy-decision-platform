"""Historical wholesale-exposure comparison for two fixed load schedules."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class Scenario:
    operating_start_hour: int = 8
    operating_end_hour: int = 20
    background_kw: float = 5.0
    flexible_kw: float = 5.0
    flexible_hours: int = 2
    original_start_hour: int = 16
    alternative_start_hour: int = 11
    max_combined_kw: float = 10.0

    def validate(self) -> None:
        if not 0 <= self.operating_start_hour < self.operating_end_hour <= 24:
            raise ValueError("Operating hours must fall within one day")
        if self.background_kw < 0 or self.flexible_kw <= 0 or self.flexible_hours <= 0:
            raise ValueError("Loads and flexible duration must be positive")
        if self.background_kw + self.flexible_kw > self.max_combined_kw:
            raise ValueError("Combined load exceeds the configured maximum")
        for start in (self.original_start_hour, self.alternative_start_hour):
            if start < self.operating_start_hour or start + self.flexible_hours > self.operating_end_hour:
                raise ValueError("A flexible window falls outside operating hours")

    @property
    def daily_kwh(self) -> float:
        return self.background_kw * (self.operating_end_hour - self.operating_start_hour) + self.flexible_kw * self.flexible_hours


def evaluate_frame(prices: pd.DataFrame, scenario: Scenario, start: date, end: date) -> dict:
    """Compare schedules on complete local days, without price-based optimisation."""
    scenario.validate()
    if start > end:
        raise ValueError("Start date must be on or before end date")
    required = {"interval_start_aest", "price_aud_per_mwh"}
    if not required.issubset(prices.columns):
        raise ValueError(f"Price input requires columns: {sorted(required)}")
    frame = prices.copy()
    frame["interval_start_aest"] = pd.to_datetime(frame["interval_start_aest"])
    if frame["interval_start_aest"].dt.tz is not None:
        frame["interval_start_aest"] = frame["interval_start_aest"].dt.tz_localize(None)
    frame["local_date"] = frame["interval_start_aest"].dt.date
    frame = frame.loc[frame["local_date"].between(start, end)]
    if frame.empty:
        raise ValueError("No prices in the requested period")

    daily = []
    excluded = []
    for day, group in frame.groupby("local_date", sort=True):
        expected = pd.date_range(str(day), periods=288, freq="5min")
        actual = pd.DatetimeIndex(group["interval_start_aest"])
        if len(actual) != 288 or not actual.is_unique or len(actual.difference(expected)) != 0:
            excluded.append(day.isoformat())
            continue
        hours = group["interval_start_aest"].dt.hour
        base = hours.between(scenario.operating_start_hour, scenario.operating_end_hour - 1).astype(float) * scenario.background_kw
        original = hours.between(scenario.original_start_hour, scenario.original_start_hour + scenario.flexible_hours - 1).astype(float) * scenario.flexible_kw
        alternative = hours.between(scenario.alternative_start_hour, scenario.alternative_start_hour + scenario.flexible_hours - 1).astype(float) * scenario.flexible_kw
        price = group["price_aud_per_mwh"].astype(float)
        # Each row is five minutes: kW / 12 = kWh, then $/MWh / 1000.
        original_aud = float((((base + original) / 12) * price / 1000).sum())
        alternative_aud = float((((base + alternative) / 12) * price / 1000).sum())
        daily.append({"date": day.isoformat(), "original_aud": round(original_aud, 6),
                      "alternative_aud": round(alternative_aud, 6),
                      "reduction_aud": round(original_aud - alternative_aud, 6)})
    if not daily:
        raise ValueError("No complete price days in the requested period")
    results = pd.DataFrame.from_records(daily)
    original_total = float(results["original_aud"].sum())
    reduction_total = float(results["reduction_aud"].sum())
    return {
        "period_start": start.isoformat(), "period_end": end.isoformat(),
        "assumptions": asdict(scenario),
        "complete_days": len(daily), "excluded_days": excluded,
        "daily_energy_kwh": scenario.daily_kwh,
        "original_total_aud": round(original_total, 2),
        "alternative_total_aud": round(float(results["alternative_aud"].sum()), 2),
        "reduction_total_aud": round(reduction_total, 2),
        "reduction_percent": round(100 * reduction_total / original_total, 2) if original_total > 0.01 else None,
        "median_daily_reduction_aud": round(float(results["reduction_aud"].median()), 2),
        "worst_daily_reduction_aud": round(float(results["reduction_aud"].min()), 2),
        "days_better_percent": round(100 * float((results["reduction_aud"] > 0).mean()), 1),
        "daily": daily,
        "interpretation": "Historical wholesale-price exposure for a hypothetical load; retail tariffs and operating costs are excluded.",
    }
