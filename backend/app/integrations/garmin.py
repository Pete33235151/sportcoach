"""Two isolated integrations: official Personal API read, unofficial opt-in workout write."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Any


def _number(payload: Any, *names: str) -> float | None:
    """Use only known fields and reject booleans, malformed and negative measurements."""
    if isinstance(payload, dict):
        for key in names:
            value = payload.get(key)
            if isinstance(value, (float, int)) and not isinstance(value, bool) and value >= 0:
                return float(value)
    return None


def _day_row(rows: Any, day: str) -> dict:
    if isinstance(rows, dict):
        for value in rows.values():
            if isinstance(value, list):
                rows = value
                break
        else:
            return rows
    if isinstance(rows, list):
        for item in rows:
            if isinstance(item, dict) and (item.get("calendarDate") == day or item.get("date") == day):
                return item
        if len(rows) == 1 and isinstance(rows[0], dict):
            return rows[0]
    return {}


def normalize_personal_health(day: str, sleep: Any, hrv: Any, summaries: Any,
                              battery: Any, stress: Any) -> dict:
    """Defensive mapping of selected documented response shapes.

    Not live-account validated; store raw payload for model inspection before trusting output.
    """
    sleep_root = sleep.get("dailySleepDTO", sleep) if isinstance(sleep, dict) else {}
    hrv_root = hrv.get("hrvSummary", hrv) if isinstance(hrv, dict) else {}
    summary = _day_row(summaries, day)
    battery_row = _day_row(battery, day)
    stress_row = _day_row(stress, day)
    seconds = _number(sleep_root, "sleepTimeSeconds", "sleepDurationInSeconds")
    sleep_hours = round(seconds / 3600, 2) if seconds is not None else None
    # Body Battery raw time series are deliberately not converted to a daily scalar blindly.
    bb = _number(battery_row, "bodyBatteryAtWakeTime", "chargedValue")
    return {
        "day": day,
        "hrv": _number(hrv_root, "lastNightAvg", "weeklyAvg"),
        "resting_hr": _number(summary, "restingHeartRate", "restingHeartRateValue"),
        "sleep_hours": sleep_hours,
        "sleep_score": _number(sleep_root.get("sleepScores", {}).get("overall", {})
                               if isinstance(sleep_root.get("sleepScores"), dict) else {}, "value"),
        "stress": _number(stress_row, "overallStressLevel", "averageStressLevel")
                  or _number(summary, "averageStressLevel"),
        "body_battery": bb,
        "readiness": None,  # Personal API has no documented Training Readiness endpoint.
        "raw": {"sleep": sleep, "hrv": hrv, "summary": summary,
                "battery": battery_row, "stress": stress_row},
        "source": "garmin_personal",
    }


def fetch_personal(days: int, api_key: str) -> tuple[list[dict], list[dict]]:
    """Read actual data using Garmin's own Apache-2.0 Python client. No writes."""
    if not api_key:
        raise ValueError("SPORTCOACH_GARMIN_PERSONAL_API_KEY fehlt")
    try:
        from garmin_personal_api import GarminPersonalApiClient, PersonalApiAuthenticator
    except ImportError as exc:
        raise RuntimeError("Bitte Paket-Extra [garmin] installieren") from exc
    today = datetime.now(ZoneInfo("Europe/Vienna")).date()
    start = today - timedelta(days=days - 1)
    with PersonalApiAuthenticator() as authenticator:
        token = authenticator.obtain_token(api_key)
    health: list[dict] = []
    with GarminPersonalApiClient(token.access_token) as client:
        # Batch lists where supported; daily data only where the API requires a date.
        summaries = client.get_daily_summaries(start.isoformat(), today.isoformat())
        batteries = client.get_daily_body_battery(start.isoformat(), today.isoformat())
        stress = client.get_daily_stress(start.isoformat(), today.isoformat())
        for i in range(days):
            day = (start + timedelta(days=i)).isoformat()
            # One failed day must not destroy the whole sync. Absence is recorded as null.
            try:
                sleep = client.get_daily_sleep(day)
            except Exception:
                sleep = {}
            try:
                hrv = client.get_daily_hrv(day)
            except Exception:
                hrv = {}
            health.append(normalize_personal_health(day, sleep, hrv, summaries, batteries, stress))
        raw_activities = client.search_activities(start=0, limit=100,
                                                 start_date=start.isoformat(), end_date=today.isoformat())
    if isinstance(raw_activities, dict):
        raw_activities = raw_activities.get("activityList", raw_activities.get("activities", []))
    activities: list[dict] = []
    for a in raw_activities if isinstance(raw_activities, list) else []:
        if not isinstance(a, dict) or a.get("activityId") is None:
            continue
        date_str = str(a.get("startTimeLocal") or a.get("startTimeGMT") or "")[:10]
        if not date_str:
            continue
        distance_m = _number(a, "distance")
        duration_s = _number(a, "duration")
        sport = a.get("activityType", {})
        sport = sport.get("typeKey", "unknown") if isinstance(sport, dict) else "unknown"
        activities.append({"external_id": str(a["activityId"]), "day": date_str,
                           "name": str(a.get("activityName") or sport)[:120],
                           "sport": sport, "distance_km": round(distance_m / 1000, 3) if distance_m else None,
                           "duration_minutes": round(duration_s / 60, 2) if duration_s else 0,
                           "avg_hr": _number(a, "averageHR"),
                           "load": _number(a, "activityTrainingLoad", "trainingLoad"),
                           "pace_sec_per_km": round(duration_s / (distance_m / 1000), 1)
                           if duration_s and distance_m else None, "source": "garmin_personal", "raw": a})
    return health, activities


def publish_running_workout(workout: dict, email: str, password: str, token_dir: str) -> int:
    """Explicitly authorized, add-only upload; never overwrites/deletes calendar items.

    Dependency/API compatibility and device sync MUST be validated on the user's account.
    """
    if workout["sport"] != "running" or workout.get("kind") not in ("easy", "long"):
        raise ValueError("Nur einfache Zeit-Dauerläufe können aktuell korrekt auf Garmin übertragen werden; komplexe Intervalle sind gesperrt")
    if not email or not password:
        raise ValueError("Garmin-Connect-Schreibzugang ist nicht konfiguriert")
    try:
        from garminconnect import Garmin
        from garminconnect.workout import (
            RunningWorkout, WorkoutSegment, create_warmup_step,
            create_interval_step, create_cooldown_step,
        )
    except ImportError as exc:
        raise RuntimeError("Bitte Paket-Extra [garmin] installieren") from exc
    client = Garmin(email, password)
    client.login(token_dir)  # Initial MFA may require CLI bootstrap. Fail closed if unavailable.
    total_s = int(workout["duration_minutes"]) * 60
    warmup = min(600, max(180, total_s // 5))
    cooldown = warmup
    steps = [create_warmup_step(float(warmup)),
             create_interval_step(duration_seconds=float(max(60, total_s - warmup - cooldown)), step_order=2),
             create_cooldown_step(float(cooldown), step_order=3)]
    payload = RunningWorkout(workoutName="SportCoach: " + workout["title"],
                             estimatedDurationInSecs=total_s,
                             workoutSegments=[WorkoutSegment(segmentOrder=1,
                                   sportType={"sportTypeId": 1, "sportTypeKey": "running"},
                                   workoutSteps=steps)])
    result = client.upload_running_workout(payload)
    workout_id = int(result["workoutId"])
    client.schedule_workout(workout_id, workout["day"])
    return workout_id
