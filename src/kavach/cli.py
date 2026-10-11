"""Terminal demo. `python -m kavach.cli --demo` runs a full simulated workday
for every persona, no AWS credentials or network required (falls back to
sample_data.json), useful for a quick sanity check and for recording the
numbers used in the demo video.
"""
from __future__ import annotations

import argparse
import json

from . import data_sources
from .corridor import compare_routes
from .personas import PERSONAS
from .simulate import simulate_shift


def main() -> None:
    ap = argparse.ArgumentParser(description="Kavach demo CLI")
    ap.add_argument("--demo", action="store_true", help="simulate a full workday for every persona")
    ap.add_argument("--locality", default="rohini")
    args = ap.parse_args()

    if args.demo:
        lat, lon = data_sources.LOCALITY_COORDS.get(args.locality, data_sources.LOCALITY_COORDS["rohini"])
        snapshot = data_sources.get_locality_snapshot(args.locality, lat, lon)
        print(f"\n=== Locality snapshot: {args.locality} ===")
        print(json.dumps(snapshot, indent=2))

        for persona in PERSONAS.values():
            result = simulate_shift(
                persona,
                base_pm25=snapshot["pm25"],
                base_temp_celsius=snapshot["temp_celsius"],
                base_humidity_pct=snapshot["relative_humidity_pct"],
            )
            print(f"\n=== {persona.name} ({persona.role}) ===")
            print(f"Total exposure by end of shift: {result['total_cigarette_equivalent']} cigarette-equivalents")
            last = result["timeline"][-1]
            print(f"Final heat risk: {last['heat_risk']}, pollution risk: {last['dose_risk']}")

        print("\n=== Route comparison (demo corridor) ===")
        print(json.dumps(compare_routes(), indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
