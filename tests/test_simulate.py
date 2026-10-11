from kavach.personas import get_persona
from kavach.simulate import simulate_shift


def test_simulate_shift_shape_and_monotonic_cumulative():
    persona = get_persona("mahesh")
    result = simulate_shift(persona, base_pm25=350, base_temp_celsius=33, base_humidity_pct=50, steps=6)
    assert result["persona_id"] == "mahesh"
    assert len(result["timeline"]) == 6
    cumulative = [step["cumulative_cigarette_equivalent"] for step in result["timeline"]]
    assert cumulative == sorted(cumulative)  # never decreases
    assert result["total_cigarette_equivalent"] == cumulative[-1]


def test_simulate_shift_rejects_bad_shift_hours():
    import pytest
    from dataclasses import replace

    persona = get_persona("rohan")
    broken = replace(persona, shift_start_hour=10, shift_end_hour=10)
    with pytest.raises(ValueError):
        simulate_shift(broken, base_pm25=300, base_temp_celsius=32, base_humidity_pct=50)
