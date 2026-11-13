"""Runtime configuration. Credentials only from environment, never exposed by API."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("true", "1", "yes", "on")


@dataclass(frozen=True)
class Settings:
    demo_mode: bool = _env_bool("SPORTCOACH_DEMO_MODE", True)
    database_url: str = os.getenv("SPORTCOACH_DATABASE_URL", "sqlite:///./sportcoach.sqlite3")
    auto_sync: bool = _env_bool("SPORTCOACH_AUTO_SYNC")
    sync_interval_minutes: int = max(30, int(os.getenv("SPORTCOACH_SYNC_INTERVAL_MINUTES", "180")))
    garmin_personal_api_key: str = os.getenv("SPORTCOACH_GARMIN_PERSONAL_API_KEY", "")
    enable_garmin_write: bool = _env_bool("SPORTCOACH_ENABLE_GARMIN_WRITE")
    garmin_email: str = os.getenv("SPORTCOACH_GARMIN_EMAIL", "")
    garmin_password: str = os.getenv("SPORTCOACH_GARMIN_PASSWORD", "")
    garmin_token_dir: str = os.getenv("SPORTCOACH_GARMIN_TOKEN_DIR", ".garmin-tokens")
    access_token: str = os.getenv("SPORTCOACH_ACCESS_TOKEN", "")
