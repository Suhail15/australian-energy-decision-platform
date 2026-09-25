"""Local reproducible workflow commands."""

from __future__ import annotations

import argparse
import json
from datetime import date

from .aemo import prepare, sync
from .paths import ROOT
from .queries import prices_for_scenario
from .scenario import Scenario, evaluate_frame
from .warehouse import export_bi, load_raw, run_dbt

DEFAULT_START = date(2025, 9, 14)
DEFAULT_END = date(2026, 9, 12)
HOLDOUT_START = date(2026, 6, 14)


def main() -> None:
    parser = argparse.ArgumentParser(description="AEMO Queensland analytical workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("sync", "run-all", "evaluate"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
        cmd.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
        if name in ("sync", "run-all"):
            cmd.add_argument("--refresh", action="store_true", help="Fetch AEMO files again, including cached files")
    for name in ("prepare", "build", "export-bi"):
        sub.add_parser(name)
    args = parser.parse_args()
    if args.command in ("sync", "run-all"):
        print(f"Source manifest: {sync(args.start, args.end, refresh=args.refresh)}")
    if args.command in ("prepare", "run-all"):
        print(json.dumps(prepare(), indent=2))
    if args.command in ("build", "run-all"):
        print(f"Warehouse: {load_raw()}")
        run_dbt()
    if args.command in ("evaluate", "run-all"):
        first = max(args.start, HOLDOUT_START)
        result = evaluate_frame(prices_for_scenario(first, args.end), Scenario(), first, args.end)
        output = ROOT / "reports" / "holdout_result.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n")
        print(f"Holdout result: {output}")
        print(json.dumps({key: value for key, value in result.items() if key != "daily"}, indent=2))
        sensitivity = evaluate_frame(prices_for_scenario(first, args.end, include_not_firm=True), Scenario(), first, args.end)
        sensitivity_path = ROOT / "reports" / "holdout_sensitivity.json"
        sensitivity_path.write_text(json.dumps(sensitivity, indent=2) + "\n")
        print(f"NOT FIRM inclusive sensitivity: {sensitivity_path}")
        print(json.dumps({key: value for key, value in sensitivity.items() if key != "daily"}, indent=2))
    if args.command in ("export-bi", "run-all"):
        print("BI exports:", *export_bi(), sep="\n")


if __name__ == "__main__":
    main()
