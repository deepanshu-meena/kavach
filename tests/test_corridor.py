from kavach.corridor import DEMO_CORRIDOR, Route, Segment, compare_routes


def test_compare_routes_returns_all_and_sorted_by_cost():
    result = compare_routes()
    assert len(result["routes"]) == len(DEMO_CORRIDOR)
    costs = [r["exposure_cost"] for r in result["routes"]]
    assert costs == sorted(costs)
    assert result["recommended_route_id"] == result["routes"][0]["id"]


def test_lower_pollution_route_is_recommended_when_clearly_better():
    clean = Route("clean", "Clean route", [Segment("s1", 2.0, pm25=50, heat_index_celsius=28)])
    dirty = Route("dirty", "Dirty route", [Segment("s1", 2.0, pm25=450, heat_index_celsius=28)])
    result = compare_routes([dirty, clean])
    assert result["recommended_route_id"] == "clean"


def test_route_length_and_eta_are_positive():
    for route in DEMO_CORRIDOR:
        assert route.length_km > 0
        assert route.estimated_minutes() > 0
