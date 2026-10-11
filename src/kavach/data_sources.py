"""Live data ingestion with a documented offline fallback.

Three public sources, matching BLUEPRINT.md section 7:
  - CPCB / OpenAQ for live PM2.5 / AQI readings
  - NASA FIRMS for active-fire detections (the stubble-burning signal)
  - Open-Meteo for temperature and humidity (free, keyless, good fit for a
    hackathon build -- see DECISIONS.md #11 on why we chose it over a
    keyed weather API)

Every function degrades to sample_data.json instead of raising, because a
live demo should never go blank just because an upstream API hiccups (the
same "graceful degradation" lesson from the First Commit hackathon).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

SAMPLE_DATA_FILE = Path(__file__).parent / "sample_data.json"
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")
HTTP_TIMEOUT = 8.0


def _load_sample() -> dict[str, Any]:
    with SAMPLE_DATA_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def get_pm25(locality: str, lat: float, lon: float) -> float:
    """Live PM2.5 for a locality via OpenAQ; falls back to sample data."""
    if OPENAQ_API_KEY:
        try:
            resp = httpx.get(
                "https://api.openaq.org/v3/locations",
                params={"coordinates": f"{lat},{lon}", "radius": 10000, "limit": 1},
                headers={"X-API-Key": OPENAQ_API_KEY},
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            # Shape depends on OpenAQ v3's response; caller should treat a
            # missing/unexpected shape as "fall through to sample data".
            return float(data["results"][0]["parameters"][0]["lastValue"])
        except Exception:
            pass
    sample = _load_sample()
    return float(sample["localities"].get(locality, sample["localities"]["rohini"])["pm25"])


def get_weather(locality: str, lat: float, lon: float) -> dict[str, float]:
    """Live temperature + humidity via Open-Meteo; falls back to sample data."""
    try:
        resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m"},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        current = resp.json()["current"]
        return {
            "temp_celsius": float(current["temperature_2m"]),
            "relative_humidity_pct": float(current["relative_humidity_2m"]),
        }
    except Exception:
        sample = _load_sample()
        loc = sample["localities"].get(locality, sample["localities"]["rohini"])
        return {
            "temp_celsius": float(loc["temp_celsius"]),
            "relative_humidity_pct": float(loc["relative_humidity_pct"]),
        }


def get_fire_signal() -> dict[str, Any]:
    """Upwind active-fire count via NASA FIRMS; falls back to sample data.

    FIRMS' area-API returns CSV, not JSON; a full implementation would parse
    that CSV and count detections in a bounding box upwind of Delhi. Without
    a registered MAP_KEY this always uses the documented sample figure.
    """
    if FIRMS_MAP_KEY:
        try:
            resp = httpx.get(
                f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_MAP_KEY}/VIIRS_SNPP_NRT/"
                "74,28,78,31/1",
                timeout=HTTP_TIMEOUT,
            )
            resp.raise_for_status()
            rows = resp.text.strip().splitlines()
            count = max(len(rows) - 1, 0)  # minus header row
            return {
                "upwind_fire_count_24h": count,
                "forecast_note": "Live NASA FIRMS detection count for the Punjab/Haryana/Delhi bounding box.",
            }
        except Exception:
            pass
    return _load_sample()["fire_signal"]


def get_locality_snapshot(locality: str, lat: float, lon: float) -> dict[str, Any]:
    """Convenience: everything the risk engine needs for one locality."""
    weather = get_weather(locality, lat, lon)
    return {
        "locality": locality,
        "pm25": get_pm25(locality, lat, lon),
        "temp_celsius": weather["temp_celsius"],
        "relative_humidity_pct": weather["relative_humidity_pct"],
        "fire_signal": get_fire_signal(),
    }


LOCALITY_COORDS: dict[str, tuple[float, float]] = {
    "rohini": (28.7041, 77.1025),
    "bawana": (28.7996, 77.0338),
    "connaught-place": (28.6315, 77.2167),
}
