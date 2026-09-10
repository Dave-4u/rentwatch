from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = f"sqlite:///{(DATA_DIR / 'rentwatch.db').as_posix()}"

# Always allow local Vite + this project's GitHub Pages origin by default
DEFAULT_CORS = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "https://dave-4u.github.io,"
    "https://Dave-4u.github.io"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "RentWatch"
    secret_key: str = "rentwatch-dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = DEFAULT_DB
    cors_origins: str = DEFAULT_CORS

    @property
    def cors_origin_list(self) -> list[str]:
        """Comma-separated CORS_ORIGINS; use * for any origin (disables credentials)."""
        parts = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "*" in parts:
            return ["*"]
        # Deduplicate while preserving order
        seen: set[str] = set()
        out: list[str] = []
        for o in parts:
            if o not in seen:
                seen.add(o)
                out.append(o)
        return out


settings = Settings()
# Guard: never accidentally use empty in-memory URL from a polluted shell
if settings.database_url in ("sqlite://", "sqlite:///", ""):
    settings.database_url = DEFAULT_DB
