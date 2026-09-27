"""Local decision-support interface over validated warehouse tables."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from energy_platform import queries
from energy_platform.scenario import Scenario, evaluate_frame

st.set_page_config(page_title="Queensland energy prices | Suhail Hussain", page_icon="⚡", layout="wide")
st.title("What if a business moved two hours of electricity use?")
st.caption("A Queensland energy-data project by Suhail Hussain · AEMO prices · invented business load")


@st.cache_data(ttl=3600)
def get_coverage():
    return queries.coverage()


@st.cache_data(ttl=3600)
def get_daily(start: date, end: date):
    return queries.daily_prices(start, end)


@st.cache_data(ttl=3600)
def get_demand(start: date, end: date):
    return queries.demand_daily(start, end)


@st.cache_data(ttl=3600)
def get_patterns():
    return queries.hourly_patterns()


try:
    coverage = get_coverage()
except Exception:
    st.error("The local warehouse is unavailable. Run the source, preparation, and build commands in the README.")
    st.stop()

first = date.fromisoformat(coverage["first_date"])
last = date.fromisoformat(coverage["last_date"])
with st.sidebar:
    st.header("Analysis period")
    selected = st.date_input("Local dates", value=(max(first, last - timedelta(days=90)), last), min_value=first, max_value=last)
    st.caption(f"Source coverage: {first} to {last} · Queensland AEST")
if not isinstance(selected, tuple) or len(selected) != 2:
    st.info("Select a start and end date.")
    st.stop()
start, end = selected

market, patterns_tab, scenario_tab, evidence = st.tabs(["Market overview", "Price patterns", "Business scenario", "Evidence"])
with market:
    st.write("Start with the market itself: these charts show regional prices and demand, not a particular business's electricity bill.")
    daily = get_daily(start, end)
    demand = get_demand(start, end)
    if daily.empty:
        st.warning("No price records in this period.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Price intervals", f"{int(daily['observed_intervals'].sum()):,}")
        c2.metric("Negative-price intervals", f"{int(daily['negative_intervals'].sum()):,}")
        c3.metric("Complete price days", int((daily["observed_intervals"] == 288).sum()))
        st.plotly_chart(px.line(daily, x="local_date", y="mean_price_aud_per_mwh", title="Daily mean wholesale price (AUD/MWh)",
                                 labels={"local_date": "Date (AEST)", "mean_price_aud_per_mwh": "AUD/MWh"}), width="stretch")
        st.plotly_chart(px.line(daily, x="local_date", y="max_price_aud_per_mwh", title="Daily maximum five-minute price (AUD/MWh)",
                                 labels={"local_date": "Date (AEST)", "max_price_aud_per_mwh": "AUD/MWh"}), width="stretch")
        st.download_button("Download daily price metrics", daily.to_csv(index=False), file_name="daily_price_metrics.csv", mime="text/csv")
    if not demand.empty:
        st.plotly_chart(px.line(demand, x="local_date", y="mean_operational_demand_mw", title="Daily mean operational demand (MW; half-hour readings)",
                                 labels={"local_date": "Date (AEST)", "mean_operational_demand_mw": "MW"}), width="stretch")
        st.caption("Demand is published at half-hour intervals and is shown separately from five-minute prices.")

with patterns_tab:
    st.write("This view shows when wholesale prices tended to be higher or lower across the whole loaded period.")
    patterns = get_patterns()
    if not patterns.empty:
        pivot = patterns.pivot(index="day_of_week", columns="local_hour", values="median_price_aud_per_mwh")
        st.plotly_chart(px.imshow(pivot, labels={"x": "Hour of day (AEST)", "y": "Day of week (Sunday = 0)", "color": "AUD/MWh"}, title="Median five-minute wholesale price"), width="stretch")
        st.caption("This heatmap summarises the full loaded dataset. Use the market page for a selected date range.")

with scenario_tab:
    st.subheader("Compare two fixed schedules")
    st.write("The example uses a hypothetical business. Results show historical wholesale-price exposure, not a retail bill.")
    c1, c2, c3 = st.columns(3)
    background_kw = c1.number_input("Background load (kW)", min_value=0.0, value=5.0, step=0.5)
    flexible_kw = c2.number_input("Flexible load (kW)", min_value=0.1, value=5.0, step=0.5)
    flexible_hours = c3.number_input("Flexible duration (hours)", min_value=1, max_value=12, value=2)
    c4, c5, c6 = st.columns(3)
    original_start = c4.number_input("Original start hour", min_value=8, max_value=19, value=16)
    alternative_start = c5.number_input("Alternative start hour", min_value=8, max_value=19, value=11)
    max_kw = c6.number_input("Maximum combined load (kW)", min_value=0.1, value=10.0, step=0.5)
    scenario = Scenario(background_kw=background_kw, flexible_kw=flexible_kw, flexible_hours=flexible_hours,
                        original_start_hour=original_start, alternative_start_hour=alternative_start,
                        max_combined_kw=max_kw)
    if st.button("Evaluate schedules", type="primary"):
        try:
            result = evaluate_frame(queries.prices_for_scenario(start, end), scenario, start, end)
            st.session_state["result"] = result
        except ValueError as exc:
            st.error(str(exc))
    result = st.session_state.get("result")
    if result and result["period_start"] == start.isoformat() and result["period_end"] == end.isoformat() and result["assumptions"] == scenario.__dict__:
        c1, c2, c3 = st.columns(3)
        c1.metric("Difference in wholesale exposure", f"${result['reduction_total_aud']:,.2f}")
        c2.metric("Days alternative was lower", f"{result['days_better_percent']:.1f}%")
        c3.metric("Complete days compared", result["complete_days"])
        st.caption(f"Daily electricity use: {result['daily_energy_kwh']:g} kWh in either schedule. Excluded incomplete days: {len(result['excluded_days'])}.")
        frame = pd.DataFrame(result["daily"])
        st.plotly_chart(px.bar(frame, x="date", y="reduction_aud", title="Daily difference in wholesale exposure (AUD; negative means alternative cost more)",
                                labels={"date": "Date (AEST)", "reduction_aud": "AUD"}), width="stretch")
        st.write(f"Worst observed daily difference: ${result['worst_daily_reduction_aud']:,.2f}. Historical results cannot predict future market prices.")
        st.download_button("Download daily scenario results", frame.to_csv(index=False), file_name="scenario_daily.csv", mime="text/csv")

with evidence:
    st.subheader("What this project can and cannot tell us")
    st.write("I built this to test a practical question, then kept the data gaps and business assumptions visible alongside the result.")
    st.markdown("""
    - Prices: [AEMO NEMWeb TradingIS reports](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-management-system-mms-data/dispatch), five-minute Queensland regional reference price (AUD/MWh).
    - Demand: [AEMO actual operational demand](https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/operational-demand-data), half-hour Queensland readings (MW).
    - Scenario load: invented for demonstration; no business meter, tariff, network charge, operating constraint, or contract is represented.
    - A fixed alternative schedule is evaluated on observed past prices. This is a historical comparison, not a real-time recommendation.
    - Source checks, data definitions, limitations, and exclusions are described in the repository's `docs/` folder.
    """)
    st.write("The market data and business load have different meanings. Regional demand is context; it is not the example business's consumption.")
