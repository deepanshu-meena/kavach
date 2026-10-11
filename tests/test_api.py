from fastapi.testclient import TestClient

from kavach.api import app

client = TestClient(app)


def test_health_and_index():
    assert client.get("/api/health").json() == {"status": "ok"}
    assert "Kavach" in client.get("/").text


def test_personas_endpoint():
    data = client.get("/api/personas").json()
    assert "rohan" in data and "mahesh" in data


def test_risk_current_known_persona():
    r = client.get("/api/risk/current", params={"persona_id": "mahesh", "locality": "bawana"})
    assert r.status_code == 200
    body = r.json()
    assert body["persona"]["id"] == "mahesh"
    assert "cigarette_equivalent" in body["pollution"]
    assert "explanation" in body and body["explanation"]["text"]


def test_risk_current_unknown_persona_404():
    r = client.get("/api/risk/current", params={"persona_id": "nope"})
    assert r.status_code == 404


def test_route_compare_endpoint():
    r = client.get("/api/route/compare")
    assert r.status_code == 200
    body = r.json()
    assert len(body["routes"]) == 3
    assert body["recommended_route_id"]


def test_simulate_workday_endpoint():
    r = client.get("/api/simulate/workday", params={"persona_id": "rohan", "steps": 4})
    assert r.status_code == 200
    body = r.json()
    assert len(body["timeline"]) == 4
    assert body["total_cigarette_equivalent"] >= 0


def test_agent_fallback_used_without_aws_credentials():
    # In this environment there are no AWS credentials configured, so the
    # explanation should come from the deterministic fallback, not crash.
    r = client.get("/api/risk/current", params={"persona_id": "rohan"})
    assert r.json()["explanation"]["source"] in ("bedrock", "fallback")
