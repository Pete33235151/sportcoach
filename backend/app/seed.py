"""Synthetic, deterministic history; never mix with real data silently."""
from datetime import date, timedelta
from math import sin
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Activity, Athlete, DailyHealth, Workout


def seed_demo(session: Session, today: date) -> None:
    if not session.get(Athlete, 1):
        session.add(Athlete(id=1, name="Demo-Athlet", goal="5 km unter 22:30",
                            weekly_km=16, note="Dienstag Schwimmkurs"))
    session.flush()
    for offset in range(55, -1, -1):
        day = today - timedelta(days=offset)
        if not session.scalar(select(DailyHealth).where(DailyHealth.athlete_id == 1,
                                                          DailyHealth.day == day)):
            stress = round(29 + 9 * sin(offset * .3), 1)
            sleep = round(7.5 + .7 * sin(offset * .5), 1)
            session.add(DailyHealth(athlete_id=1, day=day, hrv=round(58 + 6 * sin(offset*.42), 1),
                                    resting_hr=round(52 + 2 * sin(offset*.38), 1),
                                    sleep_hours=sleep, sleep_score=round(min(98, sleep * 11), 1),
                                    stress=stress, body_battery=round(78 - stress*.18),
                                    readiness=round(82 - stress*.30), source="demo"))
        if offset % 3 == 0:
            ext_id = f"demo-{day.isoformat()}"
            if not session.scalar(select(Activity).where(Activity.external_id == ext_id)):
                dist = round(4.5 + (offset % 5) * .5, 2)
                duration = round(dist * (5.7 + .1 * sin(offset)), 1)
                session.add(Activity(athlete_id=1, external_id=ext_id, day=day,
                                     sport="running", name="Demolauf", duration_minutes=duration,
                                     distance_km=dist, avg_hr=140+int(offset % 9),
                                     pace_sec_per_km=round(duration * 60 / dist),
                                     load=round(duration*1.25), source="demo"))
    session.commit()
