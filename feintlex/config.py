from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Environment-driven application settings with safe local defaults."""

    env: str = Field(default="local", alias="FEINTLEX_ENV")
    db_path: Path = Field(default=PROJECT_ROOT / "data" / "feintlex.db", alias="FEINTLEX_DB_PATH")
    log_level: str = Field(default="INFO", alias="FEINTLEX_LOG_LEVEL")
    export_dir: Path = Field(default=PROJECT_ROOT / "exports", alias="FEINTLEX_EXPORT_DIR")
    ai_provider: str = Field(default="none", alias="FEINTLEX_AI_PROVIDER")
    ollama_url: str = Field(default="http://127.0.0.1:11434", alias="FEINTLEX_OLLAMA_URL")
    ollama_model: str = Field(default="llama3.2", alias="FEINTLEX_OLLAMA_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    discord_webhook_url: str | None = Field(default=None, alias="DISCORD_WEBHOOK_URL")
    feintcommand_endpoint: str | None = Field(default=None, alias="FEINTCOMMAND_ENDPOINT")
    feintvault_endpoint: str | None = Field(default=None, alias="FEINTVAULT_ENDPOINT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def resolved_db_path(self) -> Path:
        return self._resolve_project_path(self.db_path)

    @property
    def resolved_export_dir(self) -> Path:
        return self._resolve_project_path(self.export_dir)

    @property
    def resolved_log_path(self) -> Path:
        return PROJECT_ROOT / "logs" / "feintlex.log"

    @staticmethod
    def _resolve_project_path(path: Path) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path


def get_settings() -> Settings:
    return Settings()
