from datetime import date, timedelta
from app.services.planning import plan_preview
from app.services.load import calculate_load
from app.services.analysis import aerobic_decoupling


def test_swimming_tuesday_and_consistent_week():
    rows = plan_preview(date(2026, 11, 16), 80)
    assert len(rows) == 7
    assert rows[1]["sport"] == "swimming"
    assert rows[2]["kind"] == "quality"


def test_knee_safety():
    rows = plan_preview(date(2026, 11, 16), 80, pain=6)
    assert all(x["sport"] != "running" for x in rows)
    rows = plan_preview(date(2026, 11, 16), None)
    assert all(x["kind"] != "quality" for x in rows)


def test_load_future_is_ignored():
    day = date(2026, 11, 13)
    rows = [{"day": day.isoformat(), "load": 80},
            {"day": (day+timedelta(days=1)).isoformat(), "load": 300}]
    result = calculate_load(rows, day)
    assert result["last_7d"] == 80
    assert result["last_28d"] == 80


def test_decoupling():
    rows = [{"speed_mps": 3.1 if i < 30 else 2.9, "heart_rate": 140 + i//25} for i in range(60)]
    assert aerobic_decoupling(rows)["decoupling_pct"] > 0
    assert aerobic_decoupling([])["decoupling_pct"] is None
