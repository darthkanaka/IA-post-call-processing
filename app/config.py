from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    retell_api_key: str = Field(default="", description="Retell API key for signature verification")
    google_token_json: str = Field(default="{}", description="Serialized Google OAuth token JSON")
    google_calendar_id: str = Field(default="primary", description="Target Google Calendar ID")
    environment: str = Field(default="production")
    port: int = Field(default=8000)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
