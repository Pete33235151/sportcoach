"""Conservative, preview-first seven-day multisport plans."""
from datetime import date, timedelta


TEMPLATES = {
    0: ("Lockerer Dauerlauf", "running", "easy", 38, "Zone 2, entspannt sprechen können"),
    1: ("Schwimmkurs", "swimming", "technique", 90, "Technik, Kurs nach Plan"),
    2: ("Kontrolliertes Tempotraining", "running", "quality", 45,
        "10 min einlaufen, 3 × 5 min zügig mit 3 min Trabpause, 10 min auslaufen"),
    3: ("Radfahren locker", "cycling", "easy", 40, "Locker, gleichmäßig"),
    4: ("Lockerer Dauerlauf", "running", "easy", 35, "Zone 2"),
    5: ("Längerer Dauerlauf", "running", "long", 55, "Ruhige Intensität, nicht auf Tempo drücken"),
    6: ("Beweglichkeit & Erholung", "mobility", "recovery", 20,
        "Sanfte Mobilität, schmerzfrei bleiben"),
}


def plan_preview(start: date, recovery_score: int | None, pain: int = 0,
                 locked_joint: bool = False, weekly_km: float = 15) -> list[dict]:
    result: list[dict] = []
    # Data not available -> do not schedule hard sessions.
    constrained = recovery_score is None or recovery_score < 65 or pain >= 3 or locked_joint
    for i in range(7):
        day = start + timedelta(days=i)
        title, sport, kind, duration, description = TEMPLATES[day.weekday()]
        reason = "Vorlage mit konservativer Wochenstruktur"
        if weekly_km < 20 and kind == "quality":
            duration = 35
            description = "10 min einlaufen, 3 × 4 min kontrolliert zügig, dazwischen locker, auslaufen"
            reason = "Geringer aktueller Laufumfang: reduzierter Qualitätsanteil"
        if kind == "quality" and constrained:
            title, kind, duration = "Lockerer Lauf statt Intensität", "easy", 30
            description = "Leichter Dauerlauf Zone 1–2; intensive Einheit verschoben"
            reason = "Erholungs-/Schmerzsignal: keine Intervalle"
        if sport == "running" and (pain >= 5 or locked_joint):
            title, sport, kind, duration = "Belastungsarme Alternative", "mobility", "recovery", 20
            description = "Keine Laufeinheit bei deutlichen Schmerzen/Blockade"
            reason = "Sicherheitsregel Schmerz/Blockade"
        if recovery_score is not None and recovery_score < 35 and kind != "recovery":
            title, sport, kind, duration = "Erholung statt Training", "mobility", "recovery", 15
            description = "Pause oder sehr leichte Mobilität; gebuchte Kurse ggf. aussetzen"
            reason = "Erholungsindikatoren deutlich reduziert"
        result.append({"day": day.isoformat(), "title": title, "sport": sport,
                       "kind": kind, "duration_minutes": duration, "description": description,
                       "reason": reason})
    return result
