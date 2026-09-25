"""Read-only analytical API for the prepared local warehouse."""

from __future__ import annotations

from datetime import date

import duckdb
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from . import queries
from .scenario import Scenario, evaluate_frame

app = FastAPI(title="Australian Energy Decision Platform", version="0.1.0")


class ScenarioRequest(BaseModel):
    start: date
    end: date
    operating_start_hour: int = Field(default=8, ge=0, le=23)
    operating_end_hour: int = Field(default=20, ge=1, le=24)
    background_kw: float = Field(default=5.0, ge=0, le=1000)
    flexible_kw: float = Field(default=5.0, gt=0, le=1000)
    flexible_hours: int = Field(default=2, ge=1, le=24)
    original_start_hour: int = Field(default=16, ge=0, le=23)
    alternative_start_hour: int = Field(default=11, ge=0, le=23)
    max_combined_kw: float = Field(default=10.0, gt=0, le=2000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/regions")
def regions() -> list[dict]:
    return [{"id": "QLD1", "name": "Queensland", "timezone": "Australia/Brisbane"}]


@app.get("/coverage")
def coverage() -> dict:
    try:
        return queries.coverage()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Warehouse unavailable: {exc}") from exc


@app.get("/market/summary")
def market_summary(start: date = Query(...), end: date = Query(...)) -> list[dict]:
    if start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    try:
        frame = queries.daily_prices(start, end)
        frame["local_date"] = frame["local_date"].astype(str)
        return frame.to_dict(orient="records")
    except duckdb.Error as exc:
        raise HTTPException(status_code=503, detail="Warehouse unavailable") from exc


@app.get("/market/patterns")
def market_patterns() -> list[dict]:
    try:
        return queries.hourly_patterns().to_dict(orient="records")
    except duckdb.Error as exc:
        raise HTTPException(status_code=503, detail="Warehouse unavailable") from exc


@app.post("/scenarios/evaluate")
def evaluate(request: ScenarioRequest) -> dict:
    try:
        fields = request.model_dump(exclude={"start", "end"})
        scenario = Scenario(**fields)
        return evaluate_frame(queries.prices_for_scenario(request.start, request.end), scenario, request.start, request.end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except duckdb.Error as exc:
        raise HTTPException(status_code=503, detail="Warehouse unavailable") from exc
