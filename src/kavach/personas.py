"""The three demo personas used throughout the pitch, UI and simulation.

Breathing rates are standard occupational-exposure approximations (litres of
air per minute): resting ~6, light activity ~15, moderate-to-heavy manual
labour ~25. These drive the pollution dose calculation in risk.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActivityLevel = Literal["resting", "light", "moderate", "heavy"]

BREATHING_RATE_L_PER_MIN: dict[ActivityLevel, float] = {
    "resting": 6.0,
    "light": 15.0,
    "moderate": 20.0,
    "heavy": 25.0,
}


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    role: str
    activity_level: ActivityLevel
    has_smartphone: bool  # if False, alerts also go to a dispatcher
    shift_start_hour: int
    shift_end_hour: int

    @property
    def breathing_rate(self) -> float:
        return BREATHING_RATE_L_PER_MIN[self.activity_level]


PERSONAS: dict[str, Persona] = {
    "rohan": Persona(
        id="rohan",
        name="Rohan",
        role="Food-delivery rider",
        activity_level="moderate",
        has_smartphone=True,
        shift_start_hour=9,
        shift_end_hour=21,
    ),
    "constable-singh": Persona(
        id="constable-singh",
        name="Constable Singh",
        role="Delhi Traffic Police",
        activity_level="light",
        has_smartphone=True,
        shift_start_hour=8,
        shift_end_hour=16,
    ),
    "mahesh": Persona(
        id="mahesh",
        name="Mahesh",
        role="Construction labourer",
        activity_level="heavy",
        has_smartphone=False,  # alerts route to a site supervisor instead
        shift_start_hour=7,
        shift_end_hour=18,
    ),
}


def get_persona(persona_id: str) -> Persona:
    try:
        return PERSONAS[persona_id]
    except KeyError as exc:
        raise ValueError(f"Unknown persona id: {persona_id}") from exc
