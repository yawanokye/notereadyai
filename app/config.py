from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NoteReady AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    openai_api_key: str | None = None
    openai_model: str | None = None
    max_extracted_chars: int = 160_000
    generated_files_dir: Path = Path("generated")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.generated_files_dir.mkdir(parents=True, exist_ok=True)
    return settings
