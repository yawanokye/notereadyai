from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NoteReady AI"
    app_version: str = "0.1.1"
    environment: str = "development"

    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_base_url: str = "https://api.deepseek.com"

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
        return bool(self.deepseek_api_key and self.deepseek_model)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.generated_files_dir.mkdir(parents=True, exist_ok=True)
    return settings
