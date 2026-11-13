"""Single athlete domain model; explicit unique keys for idempotent re-imports."""
from datetime import date, datetime, UTC
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Athlete(Base):
    __tablename__ = "athletes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), default="Athlet")
    goal: Mapped[str] = mapped_column(String(180), default="5 km: 4:30 min/km")
    weekly_km: Mapped[float] = mapped_column(Float, default=15)
    preferred_days: Mapped[str] = mapped_column(String(100), default="Mo, Mi, Fr, Sa")
    note: Mapped[str] = mapped_column(Text, default="Schwimmen am Dienstag")


class DailyHealth(Base):
    __tablename__ = "daily_health"
    __table_args__ = (UniqueConstraint("athlete_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), default=1)
    day: Mapped[date] = mapped_column(Date, index=True)
    hrv: Mapped[float | None] = mapped_column(Float)
    resting_hr: Mapped[float | None] = mapped_column(Float)
    sleep_hours: Mapped[float | None] = mapped_column(Float)
    sleep_score: Mapped[float | None] = mapped_column(Float)
    stress: Mapped[float | None] = mapped_column(Float)
    body_battery: Mapped[float | None] = mapped_column(Float)
    readiness: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="demo")
    received_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    raw: Mapped[dict | None] = mapped_column(JSON)


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (UniqueConstraint("external_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), default=1)
    external_id: Mapped[str] = mapped_column(String(100), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    sport: Mapped[str] = mapped_column(String(40), default="running")
    name: Mapped[str] = mapped_column(String(120))
    duration_minutes: Mapped[float] = mapped_column(Float)
    distance_km: Mapped[float | None] = mapped_column(Float)
    avg_hr: Mapped[float | None] = mapped_column(Float)
    load: Mapped[float | None] = mapped_column(Float)
    pace_sec_per_km: Mapped[float | None] = mapped_column(Float)
    hr_drift_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="demo")
    raw: Mapped[dict | None] = mapped_column(JSON)


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = (UniqueConstraint("athlete_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), default=1)
    day: Mapped[date] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(120))
    sport: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(40))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    garmin_workout_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))


class CheckIn(Base):
    __tablename__ = "checkins"
    __table_args__ = (UniqueConstraint("athlete_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    athlete_id: Mapped[int] = mapped_column(ForeignKey("athletes.id"), default=1)
    day: Mapped[date] = mapped_column(Date, index=True)
    pain: Mapped[int] = mapped_column(Integer, default=0)
    fatigue: Mapped[int] = mapped_column(Integer, default=3)
    locked_joint: Mapped[bool] = mapped_column(default=False)
    note: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None))
    action: Mapped[str] = mapped_column(String(60))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
