import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "app.db"
DEFAULT_CSV_PATH = DATA_DIR / "data.csv"
DEFAULT_BACKEND_API_URL = "http://localhost:8000"

load_dotenv(ROOT_DIR / ".env")


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))
    csv_path: Path = Path(os.getenv("TOILET_CSV_PATH", DEFAULT_CSV_PATH))
    open_api_key: str = os.getenv("OPEN_API_KEY", "")
    backend_api_url: str = os.getenv("BACKEND_API_URL", DEFAULT_BACKEND_API_URL)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
    cors_origins: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        default_origins = [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
        object.__setattr__(
            self,
            "cors_origins",
            _split_csv(os.getenv("BACKEND_CORS_ORIGINS"), default_origins),
        )


settings = Settings()
