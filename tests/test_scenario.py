from datetime import date

import pandas as pd
import pytest

from energy_platform.scenario import Scenario, evaluate_frame


def one_day(day: str = "2026-08-05", original_price: float = 200, alternative_price: float = 100) -> pd.DataFrame:
    timestamps = pd.date_range(day, periods=288, freq="5min")
    prices = []
    for timestamp in timestamps:
        price = original_price if 16 <= timestamp.hour < 18 else alternative_price if 11 <= timestamp.hour < 13 else 0
        prices.append(price)
    return pd.DataFrame({"interval_start_aest": timestamps, "price_aud_per_mwh": prices})


def test_hand_calculated_difference_and_equal_energy():
    result = evaluate_frame(one_day(), Scenario(), date(2026, 8, 5), date(2026, 8, 5))
    assert result["daily_energy_kwh"] == 70
    assert result["reduction_total_aud"] == 1.0  # 10 kWh x ($200-$100)/MWh
    assert result["complete_days"] == 1


def test_duckdb_microsecond_timestamps_are_complete():
    frame = one_day()
    frame["interval_start_aest"] = frame["interval_start_aest"].astype("datetime64[us]")
    result = evaluate_frame(frame, Scenario(), date(2026, 8, 5), date(2026, 8, 5))
    assert result["complete_days"] == 1


def test_negative_prices_and_worse_alternative():
    result = evaluate_frame(one_day(original_price=-50, alternative_price=100), Scenario(), date(2026, 8, 5), date(2026, 8, 5))
    assert result["reduction_total_aud"] == -1.5
    assert result["days_better_percent"] == 0


def test_incomplete_day_is_excluded_from_both_schedules():
    full = one_day()
    incomplete = one_day("2026-08-06").iloc[1:]
    result = evaluate_frame(pd.concat([full, incomplete]), Scenario(), date(2026, 8, 5), date(2026, 8, 6))
    assert result["complete_days"] == 1
    assert result["excluded_days"] == ["2026-08-06"]


def test_impossible_window_is_rejected():
    with pytest.raises(ValueError, match="outside operating hours"):
        Scenario(alternative_start_hour=19, flexible_hours=2).validate()


def test_power_limit_is_rejected():
    with pytest.raises(ValueError, match="exceeds"):
        Scenario(max_combined_kw=9).validate()
