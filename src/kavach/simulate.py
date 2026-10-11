"""Builds an accelerated workday timeline for one persona -- used by the demo
video and the frontend's "run simulation" button. Pure function, no I/O: it
takes a locality snapshot and projects it across the persona's shift with a
simple worsening curve (AQI climbing through the afternoon, as Delhi's does
during stubble-burning season), rather than needing N live API calls.
"""
from __future__ import annotations

from typing import Any

from .personas import Persona
from .risk import HeatReading, PollutionReading, calculate_dose, calculate_heat_risk


def simulate_shift(
    persona: Persona,
    base_pm25: float,
    base_temp_celsius: float,
    base_humidity_pct: float,
    steps: int = 8,
) -> dict[str, Any]:
    shift_hours = persona.shift_end_hour - persona.shift_start_hour
    if shift_hours <= 0:
        raise ValueError("shift_end_hour must be after shift_start_hour")
    step_hours = shift_hours / steps

    timeline: list[dict[str, Any]] = []
    cumulative_dose_ug = 0.0
    cumulative_cigarettes = 0.0
    alert_fired = False

    for i in range(steps):
        hour = persona.shift_start_hour + i * step_hours
        # AQI tends to worsen into the afternoon during stubble-burning season;
        # model a simple rise-then-plateau curve for a believable demo.
        progress = i / max(steps - 1, 1)
        pm25 = base_pm25 * (1.0 + 0.35 * progress)
        temp = base_temp_celsius * (1.0 + 0.08 * progress)

        dose = calculate_dose(
            persona, PollutionReading(pm25=pm25, minutes_outdoors=step_hours * 60)
        )
        heat = calculate_heat_risk(
            persona, HeatReading(temp_celsius=temp, relative_humidity_pct=base_humidity_pct)
        )

        cumulative_dose_ug += dose.dose_ug
        cumulative_cigarettes += dose.cigarette_equivalent

        if not alert_fired and (dose.risk in ("high", "severe") or heat.take_cover):
            alert_fired = True
            alert = True
        else:
            alert = False

        timeline.append(
            {
                "hour": round(hour, 1),
                "pm25": round(pm25, 1),
                "temp_celsius": round(temp, 1),
                "dose_risk": dose.risk,
                "heat_risk": heat.risk,
                "cumulative_cigarette_equivalent": round(cumulative_cigarettes, 2),
                "take_cover": heat.take_cover,
                "alert_fired_this_step": alert,
            }
        )

    return {
        "persona_id": persona.id,
        "persona_name": persona.name,
        "shift_start_hour": persona.shift_start_hour,
        "shift_end_hour": persona.shift_end_hour,
        "timeline": timeline,
        "total_cigarette_equivalent": round(cumulative_cigarettes, 2),
    }
