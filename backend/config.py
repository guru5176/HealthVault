"""Application configuration via environment variables."""

import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "deepseek-r1:7b"

    # MongoDB
    mongodb_uri: str = ""
    mongodb_db: str = "health_wallet"

    # MLflow
    mlflow_tracking_uri: str = "./mlflow_data"

    # App
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
