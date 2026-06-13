from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "dev"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    google_solar_api_key:      str = ""
    eumetsat_consumer_key:     str = ""
    eumetsat_consumer_secret:  str = ""
    copernicus_client_id:      str = ""
    copernicus_client_secret:  str = ""

    # Ollama — local chat inference
    ollama_base_url: str = "http://localhost:11434"
    ollama_model:    str = "llama3.2:1b"

    # Groq — market intel agent (cloud, fast, free tier)
    groq_api_key: str = ""

    @model_validator(mode="after")
    def _restrict_cors_in_prod(self) -> "Settings":
        if self.environment == "prod" and "*" in self.cors_origins:
            self.cors_origins = []
        return self


settings = Settings()
