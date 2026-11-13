from app.integrations.garmin import normalize_personal_health


def test_personal_mapping_known_fields():
    result = normalize_personal_health("2026-11-13",
        {"dailySleepDTO": {"sleepTimeSeconds": 25200, "sleepScores": {"overall": {"value": 81}}}},
        {"hrvSummary": {"lastNightAvg": 56}},
        [{"calendarDate": "2026-11-13", "restingHeartRate": 53}],
        [{"calendarDate": "2026-11-13", "bodyBatteryAtWakeTime": 76}],
        [{"calendarDate": "2026-11-13", "overallStressLevel": 22}])
    assert result["sleep_hours"] == 7
    assert result["hrv"] == 56
    assert result["resting_hr"] == 53
    assert result["body_battery"] == 76
    assert result["readiness"] is None


def test_api_endpoints(client):
    assert client.get("/health").status_code == 200
    d = client.get("/api/dashboard").json()
    assert d["data_source"] == "demo"
    assert len(d["plan"]) == 7
    assert len(client.get("/api/history").json()["health"]) >= 45
    assert client.get("/").status_code == 200
    assert client.post("/api/plan/commit", json={"confirm":False}).status_code == 400
    assert client.post("/api/garmin/publish/1",json={"confirm":True}).status_code == 403
    assert client.post("/api/garmin/sync",json={"days":7}).json()["mode"] == "demo"


def test_checkin_plan(client):
    assert client.post("/api/checkin",json={"pain":7,"fatigue":8,"locked_joint":True}).status_code == 200
    d = client.get("/api/dashboard").json()
    assert d["recovery"]["score"] <= 25
    assert all(row["sport"] != "running" for row in d["plan"])
    assert client.post("/api/plan/commit",json={"confirm":True}).status_code == 200
    assert len(client.get("/api/plan").json()) == 7
