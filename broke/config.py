from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BROKE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = "ollama/llama3.1"
    llm_base_url: str | None = None
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_path: str = "./chroma_data"
    memory_window: int = 20
    debug: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
