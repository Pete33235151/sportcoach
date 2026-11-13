from app.services.recovery import calculate_recovery


def history():
    return [{"hrv": 60, "resting_hr": 50} for _ in range(28)]


def test_good_vs_bad():
    good = calculate_recovery({"hrv": 65, "resting_hr": 49, "sleep_hours": 8,
                               "sleep_score": 90, "stress": 20, "body_battery": 92}, history())
    bad = calculate_recovery({"hrv": 40, "resting_hr": 60, "sleep_hours": 4.5,
                              "sleep_score": 40, "stress": 75, "body_battery": 25}, history())
    assert good.score is not None and bad.score is not None and good.score > bad.score


def test_missing_values_no_invention():
    r = calculate_recovery({"hrv": 55}, [])
    assert r.score is None and r.confidence == "niedrig"


def test_joint_locking_override():
    x = calculate_recovery({"hrv": 65, "resting_hr": 49, "sleep_hours": 8,
                            "stress": 20, "body_battery": 90}, history(), locked_joint=True)
    assert x.score <= 25
    assert x.cautions
