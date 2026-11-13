"""Descriptive training load indicators, no injury risk estimate."""
from datetime import date, timedelta
from math import exp


def calculate_load(activities: list[dict], today: date) -> dict:
    daily: dict[date, float] = {}
    for row in activities:
        day = row.get("day")
        if isinstance(day, str):
            day = date.fromisoformat(day)
        if day is None or day > today:
            continue
        load = row.get("load")
        if load is None:
            # Fallback is an estimated duration intensity indicator, NOT Garmin training load.
            load = float(row.get("duration_minutes") or 0) * .7
        daily[day] = daily.get(day, 0) + max(0.0, float(load))
    def total(days: int) -> float:
        return round(sum(v for k, v in daily.items() if today - timedelta(days=days - 1) <= k <= today), 1)
    # EWMA, chronologically; excludes future loads.
    atl = ctl = 0.0
    alpha7 = 1 - exp(-1 / 7)
    alpha42 = 1 - exp(-1 / 42)
    if daily:
        start = min(daily)
        for i in range((today - start).days + 1):
            load = daily.get(start + timedelta(days=i), 0)
            atl = alpha7 * load + (1 - alpha7) * atl
            ctl = alpha42 * load + (1 - alpha42) * ctl
    return {"last_24h": total(1), "last_7d": total(7), "last_28d": total(28),
            "atl_7d": round(atl, 1), "ctl_42d": round(ctl, 1),
            "form_tsb": round(ctl - atl, 1),
            "unit": "Garmin-Last falls vorhanden, sonst geschätzter Dauerindikator"}
