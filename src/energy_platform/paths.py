from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("ENERGY_PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


def database_path() -> Path:
    configured = Path(os.environ.get("ENERGY_DB_PATH", "data/warehouse/energy.duckdb"))
    return configured if configured.is_absolute() else ROOT / configured
