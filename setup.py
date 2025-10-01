from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MODEL_PROVIDER: Literal["openai", "anthropic", "bedrock", "vertex"] = "openai"
    MODEL_NAME: str = "gpt-5"

    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    REQUEST_TIMEOUT: int = 30
    LOG_LEVEL: str = "INFO"

    def require_key(self) -> None:
        if self.MODEL_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY fehlt.")
        if self.MODEL_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY fehlt.")

settings = Settings()
