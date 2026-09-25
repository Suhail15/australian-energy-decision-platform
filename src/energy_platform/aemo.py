"""AEMO NEMWeb archive discovery, download, and narrow table extraction.

The sources are nested ZIP files of MMS-style CSV reports. Only documented
TRADING.PRICE and OPERATIONAL_DEMAND.ACTUAL rows are selected.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

from .paths import PROCESSED, RAW

AEST = timezone(timedelta(hours=10))
BASE = "https://www.nemweb.com.au"
PRICE_ARCHIVE = f"{BASE}/Reports/ARCHIVE/TradingIS_Reports/"
DEMAND_ARCHIVE = f"{BASE}/Reports/ARCHIVE/Operational_Demand/ACTUAL_DAILY/"
DEMAND_CURRENT = f"{BASE}/Reports/CURRENT/Operational_Demand/ACTUAL_DAILY/"
PRICE_PATTERN = re.compile(r"PUBLIC_TRADINGIS_(\d{8})_(\d{8})\.zip$", re.I)
DEMAND_ARCHIVE_PATTERN = re.compile(r"PUBLIC_ACTUAL_OPERATIONAL_DEMAND_DAILY_(\d{8})\.zip$", re.I)
DEMAND_CURRENT_PATTERN = re.compile(r"PUBLIC_ACTUAL_OPERATIONAL_DEMAND_DAILY_(\d{8})_\d+\.zip$", re.I)


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "EnergyDecisionPlatform/0.1 (portfolio research)"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def catalog(url: str) -> list[tuple[str, str]]:
    parser = _Links()
    parser.feed(_get(url).decode("utf-8"))
    results = []
    for href in parser.hrefs:
        if not href.lower().endswith(".zip") or not href.startswith("/Reports/"):
            continue
        results.append((href.rsplit("/", 1)[-1], BASE + href))
    return sorted(set(results))


def discover(start: date, end: date) -> list[dict[str, str]]:
    """Find price bundles and operational-demand files covering local dates."""
    selected: dict[str, dict[str, str]] = {}
    for name, url in catalog(PRICE_ARCHIVE):
        match = PRICE_PATTERN.fullmatch(name)
        if match:
            bundle_start, bundle_end = (datetime.strptime(part, "%Y%m%d").date() for part in match.groups())
            # Bundles include the first 25 minutes of the following Sunday.
            if bundle_start <= end and bundle_end + timedelta(days=1) >= start:
                selected[name] = {"kind": "price", "name": name, "url": url}
    if not any(item["kind"] == "price" for item in selected.values()):
        raise ValueError("No AEMO trading-price archive bundles cover the requested period")

    for name, url in catalog(DEMAND_ARCHIVE):
        match = DEMAND_ARCHIVE_PATTERN.fullmatch(name)
        if match:
            month = datetime.strptime(match.group(1), "%Y%m%d").date()
            following = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
            # A report for a market day also contains early hours of the next day.
            if month <= end and following >= start:
                selected[name] = {"kind": "demand", "name": name, "url": url}
    for name, url in catalog(DEMAND_CURRENT):
        match = DEMAND_CURRENT_PATTERN.fullmatch(name)
        if match:
            market_day = datetime.strptime(match.group(1), "%Y%m%d").date()
            if start - timedelta(days=1) <= market_day <= end:
                selected[name] = {"kind": "demand", "name": name, "url": url}
    if not any(item["kind"] == "demand" for item in selected.values()):
        raise ValueError("No AEMO operational-demand files cover the requested period")
    return sorted(selected.values(), key=lambda x: x["name"])


def sync(start: date, end: date, refresh: bool = False) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    sources = discover(start, end)
    for item in sources:
        path = RAW / item["name"]
        if refresh or not path.exists():
            payload = _get(item["url"])
            if not zipfile.is_zipfile(io.BytesIO(payload)):
                raise ValueError(f"AEMO did not return a ZIP file: {item['url']}")
            temporary = path.with_suffix(".download")
            temporary.write_bytes(payload)
            temporary.replace(path)
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        item["bytes"] = path.stat().st_size
        item["retrieved_at_utc"] = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    manifest = {"period_start": start.isoformat(), "period_end": end.isoformat(),
                "manifest_created_at_utc": datetime.now(timezone.utc).isoformat(), "sources": sources}
    path = RAW / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def _reports(bundle: Path):
    with zipfile.ZipFile(bundle) as outer:
        for name in outer.namelist():
            content = outer.read(name)
            if name.lower().endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(content)) as inner:
                    for inner_name in inner.namelist():
                        if inner_name.lower().endswith(".csv"):
                            yield inner.read(inner_name)
            elif name.lower().endswith(".csv"):
                yield content


def _rows(report: bytes, group: str, table: str):
    reader = csv.reader(io.StringIO(report.decode("utf-8-sig")))
    fields: list[str] | None = None
    for row in reader:
        if len(row) < 5 or row[1:3] != [group, table]:
            continue
        if row[0] == "I":
            fields = row[4:]
        elif row[0] == "D":
            if fields is None or len(fields) != len(row[4:]):
                raise ValueError(f"Unexpected {group}.{table} report layout")
            yield dict(zip(fields, row[4:]))


def _local_start(end_text: str, minutes: int) -> datetime:
    end = datetime.strptime(end_text, "%Y/%m/%d %H:%M:%S").replace(tzinfo=AEST)
    return end - timedelta(minutes=minutes)


def _load_manifest(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    if not manifest.get("sources"):
        raise ValueError("Source manifest is empty")
    return manifest


def prepare(manifest_path: Path = RAW / "manifest.json") -> dict[str, int]:
    manifest = _load_manifest(manifest_path)
    start = date.fromisoformat(manifest["period_start"])
    end = date.fromisoformat(manifest["period_end"])
    prices: list[dict] = []
    demand: list[dict] = []
    for item in manifest["sources"]:
        path = RAW / item["name"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]:
            raise ValueError(f"Source checksum changed: {path.name}")
        if item["kind"] == "price":
            for report in _reports(path):
                for row in _rows(report, "TRADING", "PRICE"):
                    if row["REGIONID"] != "QLD1":
                        continue
                    local_start = _local_start(row["SETTLEMENTDATE"], 5)
                    if start <= local_start.date() <= end:
                        prices.append({
                            "region_id": "QLD1",
                            "interval_start_utc": local_start.astimezone(timezone.utc),
                            "price_aud_per_mwh": float(row["RRP"]),
                            "price_status": row.get("PRICE_STATUS", ""),
                            "invalid_flag": row.get("INVALIDFLAG", ""),
                            "source_file": item["name"],
                        })
        elif item["kind"] == "demand":
            for report in _reports(path):
                for row in _rows(report, "OPERATIONAL_DEMAND", "ACTUAL"):
                    if row["REGIONID"] != "QLD1":
                        continue
                    local_start = _local_start(row["INTERVAL_DATETIME"], 30)
                    if start <= local_start.date() <= end:
                        demand.append({
                            "region_id": "QLD1",
                            "interval_start_utc": local_start.astimezone(timezone.utc),
                            "operational_demand_mw": float(row["OPERATIONAL_DEMAND"]),
                            "demand_adjustment_mw": float(row["OPERATIONAL_DEMAND_ADJUSTMENT"] or 0),
                            "source_file": item["name"],
                        })
        else:
            raise ValueError(f"Unknown source kind: {item['kind']}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, rows in (("price", prices), ("demand", demand)):
        if not rows:
            raise ValueError(f"No {name} observations in the requested period")
        frame = pd.DataFrame.from_records(rows)
        key = ["region_id", "interval_start_utc"]
        conflicts = frame.groupby(key).nunique(dropna=False)
        value_columns = (["price_aud_per_mwh", "price_status", "invalid_flag"] if name == "price"
                         else ["operational_demand_mw", "demand_adjustment_mw"])
        if (conflicts[value_columns] > 1).any(axis=1).any():
            raise ValueError(f"Conflicting duplicate {name} observations need manual review")
        frame = frame.sort_values(key + ["source_file"]).drop_duplicates(key, keep="last")
        frame.to_parquet(PROCESSED / f"{name}.parquet", index=False)
    summary = {"price_rows": len(prices), "demand_rows": len(demand),
               "unique_price_rows": len(pd.read_parquet(PROCESSED / "price.parquet")),
               "unique_demand_rows": len(pd.read_parquet(PROCESSED / "demand.parquet"))}
    (PROCESSED / "preparation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
