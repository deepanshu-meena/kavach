import pytest

from kavach.personas import PERSONAS, get_persona
from kavach.risk import HeatReading, PollutionReading, calculate_dose, calculate_heat_risk


def test_dose_scales_with_pm25_and_time():
    p = get_persona("rohan")
    low = calculate_dose(p, PollutionReading(pm25=50, minutes_outdoors=60))
    high = calculate_dose(p, PollutionReading(pm25=400, minutes_outdoors=60))
    assert high.dose_ug > low.dose_ug
    assert high.cigarette_equivalent > low.cigarette_equivalent
    assert low.risk == "low" and high.risk == "severe"


def test_dose_scales_with_activity_level():
    reading = PollutionReading(pm25=300, minutes_outdoors=120)
    resting_dose = calculate_dose(get_persona("constable-singh"), reading)  # light
    heavy_dose = calculate_dose(get_persona("mahesh"), reading)  # heavy
    assert heavy_dose.dose_ug > resting_dose.dose_ug


def test_dose_rejects_negative_inputs():
    p = get_persona("rohan")
    with pytest.raises(ValueError):
        calculate_dose(p, PollutionReading(pm25=-1, minutes_outdoors=10))
    with pytest.raises(ValueError):
        calculate_dose(p, PollutionReading(pm25=10, minutes_outdoors=-1))


def test_dose_risk_thresholds():
    p = get_persona("rohan")
    assert calculate_dose(p, PollutionReading(pm25=50, minutes_outdoors=1)).risk == "low"
    assert calculate_dose(p, PollutionReading(pm25=150, minutes_outdoors=1)).risk == "moderate"
    assert calculate_dose(p, PollutionReading(pm25=250, minutes_outdoors=1)).risk == "high"
    assert calculate_dose(p, PollutionReading(pm25=350, minutes_outdoors=1)).risk == "severe"


def test_heat_below_threshold_is_safe():
    p = get_persona("rohan")
    result = calculate_heat_risk(p, HeatReading(temp_celsius=22, relative_humidity_pct=40))
    assert result.risk == "safe"
    assert result.take_cover is False


def test_heat_danger_triggers_take_cover():
    p = get_persona("mahesh")  # heavy exertion -> biggest exertion bump
    result = calculate_heat_risk(p, HeatReading(temp_celsius=40, relative_humidity_pct=60))
    assert result.risk in ("warning", "danger")
    assert result.take_cover is True


def test_heat_exertion_increases_risk_for_same_weather():
    weather = HeatReading(temp_celsius=34, relative_humidity_pct=55)
    light = calculate_heat_risk(get_persona("constable-singh"), weather)
    heavy = calculate_heat_risk(get_persona("mahesh"), weather)
    assert heavy.heat_index_celsius >= light.heat_index_celsius


def test_all_personas_have_valid_breathing_rates():
    for persona in PERSONAS.values():
        assert persona.breathing_rate > 0
