"""FastAPI app: static dashboard + JSON API. Run: uvicorn kavach.api:app --reload

This same app is reused on AWS Lambda via Mangum in lambda_handler.py, so
there is exactly one set of route definitions, not two (see DECISIONS.md #12).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import data_sources
from .agent import build_explanation
from .corridor import compare_routes
from .personas import PERSONAS, get_persona
from .risk import HeatReading, PollutionReading, calculate_dose, calculate_heat_risk
from .simulate import simulate_shift

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="Kavach", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/personas")
def personas() -> dict[str, Any]:
    return {
        pid: {"name": p.name, "role": p.role, "activity_level": p.activity_level}
        for pid, p in PERSONAS.items()
    }


class RiskQuery(BaseModel):
    persona_id: str
    locality: str = Field(default="rohini")
    minutes_outdoors: float = Field(default=60, ge=0, le=720)


@app.get("/api/risk/current")
def risk_current(persona_id: str, locality: str = "rohini", minutes_outdoors: float = 60) -> dict[str, Any]:
    try:
        persona = get_persona(persona_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    lat, lon = data_sources.LOCALITY_COORDS.get(locality, data_sources.LOCALITY_COORDS["rohini"])
    snapshot = data_sources.get_locality_snapshot(locality, lat, lon)

    dose = calculate_dose(
        persona, PollutionReading(pm25=snapshot["pm25"], minutes_outdoors=minutes_outdoors)
    )
    heat = calculate_heat_risk(
        persona,
        HeatReading(
            temp_celsius=snapshot["temp_celsius"],
            relative_humidity_pct=snapshot["relative_humidity_pct"],
        ),
    )

    explanation = build_explanation(
        {
            "persona_name": persona.name,
            "dose": dose.__dict__,
            "heat": heat.__dict__,
        }
    )

    return {
        "persona": {"id": persona.id, "name": persona.name, "role": persona.role},
        "locality": locality,
        "snapshot": snapshot,
        "pollution": dose.__dict__,
        "heat": heat.__dict__,
        "explanation": explanation,
    }


@app.get("/api/route/compare")
def route_compare() -> dict[str, Any]:
    return compare_routes()


@app.get("/api/simulate/workday")
def simulate_workday(persona_id: str, locality: str = "rohini", steps: int = 8) -> dict[str, Any]:
    try:
        persona = get_persona(persona_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    lat, lon = data_sources.LOCALITY_COORDS.get(locality, data_sources.LOCALITY_COORDS["rohini"])
    snapshot = data_sources.get_locality_snapshot(locality, lat, lon)

    result = simulate_shift(
        persona,
        base_pm25=snapshot["pm25"],
        base_temp_celsius=snapshot["temp_celsius"],
        base_humidity_pct=snapshot["relative_humidity_pct"],
        steps=steps,
    )
    result["locality"] = locality
    result["fire_signal"] = snapshot["fire_signal"]
    return result


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")
