"""A fixed demo corridor (see DECISIONS.md #6 for why this isn't a full
citywide routing engine): a handful of real road segments near DTU, Delhi,
each tagged with a representative PM2.5 and heat-index value so route
comparison is a real calculation on real-shaped data, not a hardcoded
answer.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    name: str
    length_km: float
    pm25: float
    heat_index_celsius: float


@dataclass(frozen=True)
class Route:
    id: str
    label: str
    segments: list[Segment]

    @property
    def length_km(self) -> float:
        return round(sum(s.length_km for s in self.segments), 2)

    @property
    def avg_pm25(self) -> float:
        total = sum(s.length_km * s.pm25 for s in self.segments)
        return round(total / self.length_km, 1) if self.length_km else 0.0

    @property
    def avg_heat_index(self) -> float:
        total = sum(s.length_km * s.heat_index_celsius for s in self.segments)
        return round(total / self.length_km, 1) if self.length_km else 0.0

    def estimated_minutes(self, avg_speed_kmh: float = 22.0) -> float:
        return round((self.length_km / avg_speed_kmh) * 60.0, 1)

    def exposure_cost(self, pollution_weight: float = 0.7, heat_weight: float = 0.3) -> float:
        """Lower is better. Weighted sum of length-weighted PM2.5 and heat
        exposure along the route -- pollution weighted higher by default
        since this project submits under the Air track."""
        pollution_term = sum(s.length_km * s.pm25 for s in self.segments)
        heat_term = sum(s.length_km * s.heat_index_celsius for s in self.segments)
        return round(pollution_weight * pollution_term + heat_weight * heat_term, 1)


# Demo corridor: Rohini / Bawana Road area, near DTU -- three real-feeling
# options between the same two points, with different exposure profiles.
DEMO_CORRIDOR: list[Route] = [
    Route(
        id="route-a",
        label="Bawana Road (direct)",
        segments=[
            Segment("Bawana Road stretch 1", 2.1, pm25=410, heat_index_celsius=34),
            Segment("Bawana Road stretch 2", 1.8, pm25=430, heat_index_celsius=35),
        ],
    ),
    Route(
        id="route-b",
        label="Via Rohini Sector service road",
        segments=[
            Segment("Sector service road", 2.4, pm25=290, heat_index_celsius=32),
            Segment("Tree-lined residential stretch", 1.9, pm25=250, heat_index_celsius=30),
        ],
    ),
    Route(
        id="route-c",
        label="Via Outer Ring Road",
        segments=[
            Segment("Outer Ring Road stretch 1", 3.0, pm25=380, heat_index_celsius=33),
            Segment("Outer Ring Road stretch 2", 1.2, pm25=360, heat_index_celsius=33),
        ],
    ),
]


def compare_routes(corridor: list[Route] | None = None) -> dict:
    routes = corridor if corridor is not None else DEMO_CORRIDOR
    scored = [
        {
            "id": r.id,
            "label": r.label,
            "length_km": r.length_km,
            "estimated_minutes": r.estimated_minutes(),
            "avg_pm25": r.avg_pm25,
            "avg_heat_index_celsius": r.avg_heat_index,
            "exposure_cost": r.exposure_cost(),
        }
        for r in routes
    ]
    scored.sort(key=lambda r: r["exposure_cost"])
    recommended = scored[0]["id"] if scored else None
    return {"routes": scored, "recommended_route_id": recommended}
