"""Transparent recovery indicator, NOT a medical readiness diagnosis."""
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class RecoveryResult:
    score: int | None
    category: str
    confidence: str
    coverage: int
    components: dict[str, float]
    reasons: list[str]
    cautions: list[str]

    def as_dict(self) -> dict:
        return {
            "score": self.score, "category": self.category, "confidence": self.confidence,
            "coverage": self.coverage, "components": self.components,
            "reasons": self.reasons, "cautions": self.cautions,
        }


def _clip(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _baseline(history: list[dict], field: str) -> float | None:
    values = [float(row[field]) for row in history[-28:] if row.get(field) is not None]
    return median(values) if len(values) >= 7 else None


def calculate_recovery(today: dict, history: list[dict], recent_load: float = 0,
                       pain: int = 0, locked_joint: bool = False) -> RecoveryResult:
    """Personal 28-day baselines, robust missing-data handling, conservative overrides.

    Each component describes a signal. Do not interpret as physiological certainty.
    """
    parts: dict[str, float] = {}
    weights = {"hrv": 0.26, "resting_hr": 0.18, "sleep": 0.23,
               "stress": 0.11, "body_battery": 0.12, "load": 0.10}
    reasons: list[str] = []
    cautions: list[str] = []

    hrv_base = _baseline(history, "hrv")
    hrv = today.get("hrv")
    if hrv is not None and hrv_base:
        delta = (float(hrv) / hrv_base - 1) * 100
        parts["hrv"] = _clip(72 + delta * 2)
        reasons.append(f"HRV {delta:+.1f} % gegenüber persönlicher Baseline")
    elif hrv is not None:
        cautions.append("HRV-Baseline: weniger als sieben historische Tage")

    hr_base = _baseline(history, "resting_hr")
    hr = today.get("resting_hr")
    if hr is not None and hr_base:
        delta = float(hr) - hr_base
        parts["resting_hr"] = _clip(76 - delta * 7)
        reasons.append(f"Ruhepuls {delta:+.0f} bpm gegenüber persönlicher Baseline")

    sleep_hours = today.get("sleep_hours")
    sleep_score = today.get("sleep_score")
    if sleep_hours is not None:
        s = _clip(70 + (float(sleep_hours) - 7.5) * 18)
        if sleep_score is not None:
            s = .65 * s + .35 * _clip(float(sleep_score))
        parts["sleep"] = round(s, 1)
        reasons.append(f"Schlaf {float(sleep_hours):.1f} h")
    elif sleep_score is not None:
        parts["sleep"] = _clip(float(sleep_score))

    if today.get("stress") is not None:
        parts["stress"] = _clip(95 - float(today["stress"]) * .85)
    if today.get("body_battery") is not None:
        parts["body_battery"] = _clip(float(today["body_battery"]))
    if history and recent_load >= 0:
        # Daily load is an auxiliary signal; this score cannot be a injury-risk model.
        parts["load"] = _clip(82 - max(0.0, recent_load - 60) * .22)

    coverage = len(parts)
    if coverage < 2:
        return RecoveryResult(None, "nicht genügend Daten", "niedrig", coverage,
                              parts, reasons, [*cautions, "Keine belastbare Recovery-Bewertung möglich"])
    weighted = sum(parts[k] * weights[k] for k in parts) / sum(weights[k] for k in parts)
    score = round(_clip(weighted))
    if locked_joint:
        cautions.append("Gelenkblockade gemeldet: belastendes Training pausieren und medizinisch abklären")
        score = min(score, 25)
    elif pain >= 5:
        cautions.append("Schmerzen ≥5/10: keine harte Laufbelastung empfehlen")
        score = min(score, 45)
    elif pain >= 3:
        cautions.append("Schmerzen 3–4/10: Training vorsichtig anpassen")
        score = min(score, 65)
    category = ("erholt" if score >= 80 else "normal" if score >= 65 else
                "reduzieren" if score >= 50 else "locker" if score >= 35 else "pausieren")
    confidence = "hoch" if coverage >= 5 and hrv_base and hr_base else "mittel" if coverage >= 4 else "niedrig"
    return RecoveryResult(score, category, confidence, coverage, parts, reasons, cautions)
