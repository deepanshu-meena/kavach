"""Pure, deterministic risk calculations. No network calls, no AI -- these are
the "hard to fake" numbers the whole pitch rests on. Every function here is
unit-tested in tests/test_risk.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .personas import Persona

PollutionRisk = Literal["low", "moderate", "high", "severe"]
HeatRisk = Literal["safe", "caution", "warning", "danger"]

# Berkeley Earth approximation: sustained exposure to 22 ug/m3 of PM2.5 for
# 24 hours is roughly equivalent to smoking 1 cigarette, i.e. ~528 ug-hours/m3
# per cigarette. We scale *time* by how much harder the person is breathing
# relative to resting, since the Berkeley figure assumes ordinary breathing.
UG_HOURS_PER_CIGARETTE = 22.0 * 24.0
RESTING_BREATHING_RATE = 6.0  # L/min, matches personas.BREATHING_RATE_L_PER_MIN["resting"]


@dataclass(frozen=True)
class PollutionReading:
    pm25: float  # ug/m3, ambient
    minutes_outdoors: float


@dataclass(frozen=True)
class DoseResult:
    dose_ug: float
    cigarette_equivalent: float
    risk: PollutionRisk


def calculate_dose(persona: Persona, reading: PollutionReading) -> DoseResult:
    """Convert ambient PM2.5 + how hard someone is breathing + time outdoors
    into an actual inhaled dose, expressed as cigarette-equivalents.
    """
    if reading.pm25 < 0 or reading.minutes_outdoors < 0:
        raise ValueError("pm25 and minutes_outdoors must be non-negative")

    volume_inhaled_m3 = (persona.breathing_rate * reading.minutes_outdoors) / 1000.0
    dose_ug = reading.pm25 * volume_inhaled_m3

    effective_hours = (reading.minutes_outdoors / 60.0) * (
        persona.breathing_rate / RESTING_BREATHING_RATE
    )
    cigarette_equivalent = (reading.pm25 * effective_hours) / UG_HOURS_PER_CIGARETTE

    if reading.pm25 >= 300:
        risk: PollutionRisk = "severe"
    elif reading.pm25 >= 200:
        risk = "high"
    elif reading.pm25 >= 100:
        risk = "moderate"
    else:
        risk = "low"

    return DoseResult(
        dose_ug=round(dose_ug, 2),
        cigarette_equivalent=round(cigarette_equivalent, 2),
        risk=risk,
    )


@dataclass(frozen=True)
class HeatReading:
    temp_celsius: float
    relative_humidity_pct: float


@dataclass(frozen=True)
class HeatResult:
    heat_index_celsius: float
    risk: HeatRisk
    take_cover: bool


def _heat_index_fahrenheit(temp_f: float, rh: float) -> float:
    """NOAA/Rothfusz regression for heat index (valid above ~80F / ~27C)."""
    hi = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f * temp_f
        - 0.05481717 * rh * rh
        + 0.00122874 * temp_f * temp_f * rh
        + 0.00085282 * temp_f * rh * rh
        - 0.00000199 * temp_f * temp_f * rh * rh
    )
    return hi


def calculate_heat_risk(persona: Persona, reading: HeatReading) -> HeatResult:
    """Approximate heat-stress risk (a simplified stand-in for full WBGT --
    see DECISIONS.md #3) from temperature, humidity and exertion level.

    Below 27C the Rothfusz regression isn't valid, so we just use the
    measured temperature there -- the body isn't under heat stress at that
    point regardless of humidity.
    """
    if reading.temp_celsius < 27:
        heat_index_c = reading.temp_celsius
    else:
        temp_f = reading.temp_celsius * 9.0 / 5.0 + 32.0
        hi_f = _heat_index_fahrenheit(temp_f, reading.relative_humidity_pct)
        heat_index_c = (hi_f - 32.0) * 5.0 / 9.0

    # Exertion pushes real physiological heat load above what the ambient
    # heat index alone implies; nudge the effective index up for harder work.
    exertion_bump = {"resting": 0.0, "light": 1.0, "moderate": 2.5, "heavy": 4.0}
    effective_index = heat_index_c + exertion_bump[persona.activity_level]

    if effective_index >= 41:
        risk: HeatRisk = "danger"
    elif effective_index >= 37:
        risk = "warning"
    elif effective_index >= 32:
        risk = "caution"
    else:
        risk = "safe"

    return HeatResult(
        heat_index_celsius=round(heat_index_c, 1),
        risk=risk,
        take_cover=risk in ("warning", "danger"),
    )
