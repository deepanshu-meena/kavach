from kavach import data_sources


def test_get_pm25_falls_back_to_sample_data_without_key(monkeypatch):
    monkeypatch.setattr(data_sources, "OPENAQ_API_KEY", "")
    value = data_sources.get_pm25("rohini", *data_sources.LOCALITY_COORDS["rohini"])
    assert value > 0


def test_get_weather_falls_back_when_network_unreachable(monkeypatch):
    import httpx

    def boom(*args, **kwargs):
        raise httpx.ConnectError("no network in this environment")

    monkeypatch.setattr(httpx, "get", boom)
    weather = data_sources.get_weather("bawana", *data_sources.LOCALITY_COORDS["bawana"])
    assert "temp_celsius" in weather and "relative_humidity_pct" in weather


def test_get_fire_signal_without_key_uses_sample():
    data_sources.FIRMS_MAP_KEY = ""
    signal = data_sources.get_fire_signal()
    assert "upwind_fire_count_24h" in signal


def test_get_locality_snapshot_shape():
    snap = data_sources.get_locality_snapshot("rohini", *data_sources.LOCALITY_COORDS["rohini"])
    assert {"locality", "pm25", "temp_celsius", "relative_humidity_pct", "fire_signal"} <= snap.keys()
