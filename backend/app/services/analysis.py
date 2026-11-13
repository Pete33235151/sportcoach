"""Activity sample analysis with defensible validity checks."""
from statistics import median


def aerobic_decoupling(samples: list[dict]) -> dict:
    """Compare HR/pace efficiency of first and second halves; excludes stopped samples.

    The result is an approximation, not a laboratory measurement. Prefer steady efforts.
    """
    rows = [r for r in samples if 70 <= float(r.get("heart_rate") or 0) <= 220
            and 1 <= float(r.get("speed_mps") or 0) <= 7]
    if len(rows) < 40:
        return {"decoupling_pct": None, "reason": "Mindestens 40 gültige Bewegungs-Samples nötig"}
    midpoint = len(rows) // 2
    def efficiency(chunk: list[dict]) -> float:
        return median(float(r["speed_mps"]) / float(r["heart_rate"]) for r in chunk)
    first = efficiency(rows[:midpoint])
    second = efficiency(rows[midpoint:])
    return {"decoupling_pct": round(100 * (1 - second / first), 2),
            "reason": "Schätzung aus Tempo/Herzfrequenz; nur für gleichmäßige Läufe sinnvoll"}
