"""SportCoach API and mobile PWA. Sensitive operations intentionally opt-in."""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timedelta, UTC
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import Settings
from .database import Base, SessionLocal, engine, get_session
from .integrations.garmin import fetch_personal, publish_running_workout
from .models import Activity, Athlete, AuditEvent, CheckIn, DailyHealth, Workout
from .seed import seed_demo
from .services.load import calculate_load
from .services.planning import plan_preview
from .services.recovery import calculate_recovery
from .services.fit import analyze_fit_bytes, MAX_UPLOAD_BYTES

settings = Settings()
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
TZ = ZoneInfo("Europe/Vienna")


def today_local() -> date:
    return datetime.now(TZ).date()


def dump_row(row, *attrs: str) -> dict:
    result = {key: getattr(row, key) for key in attrs}
    for key, val in result.items():
        if isinstance(val, (date, datetime)):
            result[key] = val.isoformat()
    return result


def health_data(session: Session, n: int = 90) -> list[dict]:
    source = "demo" if settings.demo_mode else "garmin_personal"
    rows = session.scalars(select(DailyHealth).where(DailyHealth.source == source)
                           .order_by(DailyHealth.day.desc()).limit(n)).all()
    cols = ("day", "hrv", "resting_hr", "sleep_hours", "sleep_score", "stress",
            "body_battery", "readiness", "source", "received_at")
    return [dump_row(row, *cols) for row in reversed(rows)]


def activities_data(session: Session, n: int = 100) -> list[dict]:
    source = "demo" if settings.demo_mode else "garmin_personal"
    rows = session.scalars(select(Activity).where(Activity.source == source)
                           .order_by(Activity.day.desc()).limit(n)).all()
    return [dump_row(row, "id", "external_id", "day", "sport", "name", "duration_minutes",
                     "distance_km", "avg_hr", "load", "pace_sec_per_km", "hr_drift_pct") for row in rows]


def checkin_data(session: Session) -> dict:
    row = session.scalar(select(CheckIn).where(CheckIn.day == today_local(), CheckIn.athlete_id == 1))
    return {"pain": row.pain, "fatigue": row.fatigue, "locked_joint": row.locked_joint,
            "note": row.note} if row else {"pain": 0, "fatigue": 3, "locked_joint": False, "note": ""}


def coach_state(session: Session) -> dict:
    history = health_data(session)
    today = next((r for r in history if r["day"] == today_local().isoformat()), None)
    if today is None:
        today = history[-1] if history else {}
    past = [r for r in history if r["day"] < today.get("day", "9999")]
    acts = activities_data(session)
    loads = calculate_load(acts, today_local())
    checkin = checkin_data(session)
    result = calculate_recovery(today, past, loads["last_24h"],
                                checkin["pain"], checkin["locked_joint"])
    recovery = result.as_dict()
    # No hard sessions using old measurements after a disconnected watch.
    if today.get("day"):
        gap = (today_local() - date.fromisoformat(today["day"])).days
        if gap > 1:
            recovery["score"] = None
            recovery["category"] = "Daten veraltet"
            recovery["confidence"] = "niedrig"
            recovery["cautions"].append(f"Letzte Messwerte sind {gap} Tage alt; keine Intensität empfehlen")
    return {"recovery": recovery, "load": loads, "checkin": checkin,
            "health": today, "data_last_day": history[-1]["day"] if history else None,
            "data_source": "demo" if settings.demo_mode else "garmin_personal"}


def perform_sync(session: Session, days: int) -> dict:
    if settings.demo_mode:
        return {"mode": "demo", "message": "Demo-Daten; kein Garmin-Zugriff", "imported": 0}
    if not settings.garmin_personal_api_key:
        raise ValueError("Personal API Key fehlt; bitte nur lokal in .env setzen")
    health, activities = fetch_personal(days, settings.garmin_personal_api_key)
    imported_health = imported_activities = 0
    for h in health:
        d = date.fromisoformat(h["day"])
        row = session.scalar(select(DailyHealth).where(DailyHealth.day == d, DailyHealth.athlete_id == 1))
        if row is None:
            row = DailyHealth(day=d, athlete_id=1, source="garmin_personal")
            session.add(row)
        elif row.source == "demo":
            # Never blend synthetic values with real partial measurements.
            for field in ("hrv", "resting_hr", "sleep_hours", "sleep_score", "stress", "body_battery", "readiness"):
                setattr(row, field, None)
        row.source = "garmin_personal"
        for field in ("hrv", "resting_hr", "sleep_hours", "sleep_score", "stress", "body_battery", "readiness"):
            value = h.get(field)
            if value is not None:  # Don't erase previously valid values on partial fetch.
                setattr(row, field, value)
        row.raw = h.get("raw")
        row.received_at = datetime.now(UTC).replace(tzinfo=None)
        imported_health += 1
    for a in activities:
        row = session.scalar(select(Activity).where(Activity.external_id == a["external_id"]))
        if row is None:
            row = Activity(athlete_id=1, external_id=a["external_id"], day=date.fromisoformat(a["day"]),
                           name=a["name"], duration_minutes=a["duration_minutes"], sport=a["sport"])
            session.add(row)
        for field in ("name", "sport", "duration_minutes", "distance_km", "avg_hr", "load", "pace_sec_per_km"):
            if a.get(field) is not None:
                setattr(row, field, a[field])
        row.raw, row.source = a["raw"], "garmin_personal"
        imported_activities += 1
    session.add(AuditEvent(action="garmin_sync", detail={"days": days, "health": imported_health,
                                                         "activities": imported_activities}))
    session.commit()
    return {"mode": "garmin_personal", "health_processed": imported_health,
            "activities_processed": imported_activities,
            "message": "Import beendet; Feldzuordnung mit Live-Daten prüfen"}


def _background_import() -> None:
    with SessionLocal() as session:
        perform_sync(session, 3)


async def _scheduler():
    while True:
        if not settings.demo_mode:
            try:
                # The SQLAlchemy Session is created and used in the same worker thread.
                await asyncio.to_thread(_background_import)
            except Exception:
                # Never leak exception payloads which may contain auth information.
                print("SportCoach: automatischer Garmin-Import fehlgeschlagen")
        await asyncio.sleep(settings.sync_interval_minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as s:
        if settings.demo_mode:
            seed_demo(s, today_local())
        elif not s.get(Athlete, 1):
            s.add(Athlete(id=1, name="Mein Profil"))
            s.commit()
    task = asyncio.create_task(_scheduler()) if settings.auto_sync else None
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="SportCoach", version="0.3.0", lifespan=lifespan)


@app.middleware("http")
async def access_guard(request: Request, call_next):
    # API is single-user. For network exposure configure strong auth and HTTPS reverse proxy.
    if settings.access_token and request.url.path.startswith("/api/"):
        from fastapi.responses import JSONResponse
        import secrets
        provided = request.headers.get("X-SportCoach-Token", "")
        if not secrets.compare_digest(provided, settings.access_token):
            return JSONResponse({"detail": "Nicht autorisiert"}, status_code=401)
    return await call_next(request)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.3.0"}


@app.get("/api/status")
def status():
    return {"mode": "demo" if settings.demo_mode else "garmin_personal",
            "auto_sync": settings.auto_sync,
            "sync_interval_minutes": settings.sync_interval_minutes,
            "read_configured": bool(settings.garmin_personal_api_key),
            "write_enabled": settings.enable_garmin_write}


@app.get("/api/dashboard")
def dashboard(session: Session = Depends(get_session)):
    state = coach_state(session)
    athlete = session.get(Athlete, 1)
    state["athlete"] = dump_row(athlete, "name", "goal", "weekly_km", "note") if athlete else None
    state["plan"] = plan_preview(today_local(), state["recovery"]["score"],
                                  state["checkin"]["pain"], state["checkin"]["locked_joint"],
                                  athlete.weekly_km if athlete else 15)
    state["activity_count"] = len(activities_data(session))
    return state


@app.get("/api/history")
def history(session: Session = Depends(get_session)):
    return {"health": health_data(session, 90), "activities": activities_data(session, 100)}


@app.get("/api/activities")
def activities(session: Session = Depends(get_session)):
    return activities_data(session)


@app.get("/api/plan")
def planned(session: Session = Depends(get_session)):
    rows = session.scalars(select(Workout).where(Workout.day >= today_local())
                           .order_by(Workout.day).limit(14)).all()
    return [dump_row(row, "id", "day", "title", "sport", "kind", "duration_minutes",
                     "description", "reason", "status", "garmin_workout_id") for row in rows]


class CheckInPayload(BaseModel):
    pain: int = Field(0, ge=0, le=10)
    fatigue: int = Field(3, ge=0, le=10)
    locked_joint: bool = False
    note: str = Field("", max_length=500)


@app.post("/api/checkin")
def checkin(payload: CheckInPayload, session: Session = Depends(get_session)):
    item = session.scalar(select(CheckIn).where(CheckIn.day == today_local(), CheckIn.athlete_id == 1))
    if item is None:
        item = CheckIn(athlete_id=1, day=today_local())
        session.add(item)
    for key, val in payload.model_dump().items():
        setattr(item, key, val)
    session.commit()
    return {"saved": True, "recovery": coach_state(session)["recovery"]}


class CommitPayload(BaseModel):
    confirm: bool = False


@app.post("/api/plan/commit")
def commit_plan(payload: CommitPayload, session: Session = Depends(get_session)):
    if not payload.confirm:
        raise HTTPException(400, "Bitte Trainingsplan erst prüfen und ausdrücklich bestätigen")
    state = coach_state(session)
    athlete = session.get(Athlete, 1)
    new_plan = plan_preview(today_local(), state["recovery"]["score"],
                            state["checkin"]["pain"], state["checkin"]["locked_joint"],
                            athlete.weekly_km if athlete else 15)
    for row in new_plan:
        day = date.fromisoformat(row["day"])
        item = session.scalar(select(Workout).where(Workout.day == day, Workout.athlete_id == 1))
        if item is None:
            item = Workout(day=day, athlete_id=1, title=row["title"], sport=row["sport"],
                           kind=row["kind"], duration_minutes=row["duration_minutes"],
                           description=row["description"], reason=row["reason"])
            session.add(item)
        elif item.garmin_workout_id is not None or item.status != "planned":
            continue  # Never silently overwrite a Garmin-sent or completed workout.
        else:
            for key in ("title", "sport", "kind", "duration_minutes", "description", "reason"):
                setattr(item, key, row[key])
    session.add(AuditEvent(action="commit_plan", detail={"days": 7}))
    session.commit()
    return {"saved": True, "days": 7, "message": "Nur lokaler Plan aktualisiert"}


class SyncPayload(BaseModel):
    days: int = Field(7, ge=1, le=28)


@app.post("/api/garmin/sync")
def garmin_sync(payload: SyncPayload, session: Session = Depends(get_session)):
    try:
        return perform_sync(session, payload.days)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        # Don't expose credentials/tokens or potentially sensitive response bodies.
        raise HTTPException(502, "Garmin-Import fehlgeschlagen; Server-Log prüfen") from exc


class PublishPayload(BaseModel):
    confirm: bool = False


@app.post("/api/garmin/publish/{workout_id}")
def garmin_publish(workout_id: int, payload: PublishPayload, session: Session = Depends(get_session)):
    if settings.demo_mode or not settings.enable_garmin_write:
        raise HTTPException(403, "Garmin-Schreibzugriff ist deaktiviert")
    if not payload.confirm:
        raise HTTPException(400, "Ausdrückliche Bestätigung erforderlich")
    item = session.get(Workout, workout_id)
    if not item or item.day < today_local():
        raise HTTPException(404, "Künftiges Workout nicht gefunden")
    if item.garmin_workout_id is not None:
        raise HTTPException(409, "Bereits an Garmin gesendet")
    row = dump_row(item, "day", "title", "sport", "kind", "duration_minutes")
    try:
        garmin_id = publish_running_workout(row, settings.garmin_email,
                                           settings.garmin_password, settings.garmin_token_dir)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "Garmin-Schreibvorgang fehlgeschlagen; bitte Garmin-Kalender prüfen") from exc
    item.garmin_workout_id = garmin_id
    item.status = "sent"
    session.add(AuditEvent(action="publish_workout", detail={"workout_id": workout_id,
                                                             "garmin_workout_id": garmin_id}))
    session.commit()
    return {"sent": True, "garmin_workout_id": garmin_id}


@app.get("/api/export")
def export_data(session: Session = Depends(get_session)):
    # Local owner export; deployment must supply authentication.
    return {"health": health_data(session), "activities": activities_data(session),
            "workouts": planned(session)}



class AthleteUpdate(BaseModel):
    goal: str = Field(min_length=2, max_length=180)
    weekly_km: float = Field(ge=0, le=250)


@app.post("/api/athlete")
def update_athlete(payload: AthleteUpdate, session: Session = Depends(get_session)):
    athlete = session.get(Athlete, 1)
    if athlete is None:
        raise HTTPException(404, "Profil nicht gefunden")
    athlete.goal = payload.goal
    athlete.weekly_km = payload.weekly_km
    session.add(AuditEvent(action="update_athlete", detail={"weekly_km": payload.weekly_km}))
    session.commit()
    return {"saved": True, "goal": athlete.goal, "weekly_km": athlete.weekly_km}


@app.post("/api/analysis/fit")
async def fit_analysis(request: Request):
    """Upload FIT/ZIP as application/octet-stream; raw route data never persisted."""
    chunks = bytearray()
    async for piece in request.stream():
        chunks.extend(piece)
        if len(chunks) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "Upload zu groß")
    try:
        return analyze_fit_bytes(bytes(chunks))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(501, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(422, "FIT konnte nicht dekodiert werden") from exc


app.mount("/assets", StaticFiles(directory=str(FRONTEND)), name="frontend-assets")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
