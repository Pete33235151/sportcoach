"""Safe FIT extraction and optional record-level analysis (no persisting raw GPS track)."""
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from .analysis import aerobic_decoupling

MAX_UPLOAD_BYTES = 12 * 1024 * 1024
MAX_FIT_BYTES = 32 * 1024 * 1024


def extract_fit(blob: bytes) -> bytes:
    """Accept a direct FIT or a Garmin ZIP; never unpack files onto disk."""
    if not blob or len(blob) > MAX_UPLOAD_BYTES:
        raise ValueError("FIT-Upload ist leer oder zu groß (maximal 12 MB)")
    if blob[:2] != b"PK":
        if len(blob) >= 12 and blob[8:12] == b".FIT":
            return blob
        raise ValueError("Keine FIT-Datei oder Garmin-ZIP erkannt")
    try:
        with ZipFile(BytesIO(blob)) as archive:
            files = [i for i in archive.infolist() if i.filename.lower().endswith(".fit") and not i.is_dir()]
            if len(files) != 1:
                raise ValueError("ZIP muss genau eine FIT-Datei enthalten")
            entry = files[0]
            if entry.file_size > MAX_FIT_BYTES:
                raise ValueError("FIT in ZIP zu groß")
            with archive.open(entry) as handle:
                data = handle.read(MAX_FIT_BYTES + 1)
            if len(data) > MAX_FIT_BYTES or len(data) < 12 or data[8:12] != b".FIT":
                raise ValueError("Ungültige FIT-Daten in ZIP")
            return data
    except BadZipFile as exc:
        raise ValueError("Ungültiges ZIP-Archiv") from exc


def analyze_fit_bytes(blob: bytes) -> dict:
    data = extract_fit(blob)
    try:
        import fitdecode
    except ImportError as exc:
        raise RuntimeError("FIT-Analyse benötigt das Extra: pip install -e '.[garmin]'") from exc
    samples = []
    with fitdecode.FitReader(BytesIO(data)) as reader:
        for frame in reader:
            if not isinstance(frame, fitdecode.FitDataMessage) or frame.name != "record":
                continue
            try:
                hr = frame.get_value("heart_rate")
                speed = frame.get_value("enhanced_speed") or frame.get_value("speed")
            except (KeyError, ValueError):
                continue
            if hr is not None and speed is not None:
                samples.append({"heart_rate": hr, "speed_mps": speed})
            if len(samples) > 300_000:
                raise ValueError("Zu viele FIT-Samples")
    result = aerobic_decoupling(samples)
    result["sample_count"] = len(samples)
    result["warning"] = "Entkopplung nur bei annähernd gleichmäßiger Belastung sinnvoll"
    return result
