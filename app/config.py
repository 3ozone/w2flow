"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""
    # App
    app_env: str = "development"
    app_debug: bool = True

    # Base de datos
    database_url: str = ""

    # API Portal PSCP (contractaciopublica.cat)
    pscp_portal_base_url: str = "https://contractaciopublica.cat/portal-api"
    licitation_api_timeout: int = 30
    licitation_api_max_retries: int = 2

    # Notificaciones
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_recipients: str = ""

    # Timbal LLM — model i clau API configurables via .env
    # Canviar de model = solo canviar LLM_MODEL + LLM_API_KEY al .env
    # Providers amb PDF natiu: google, anthropic
    # Providers via extracció de text (pymupdf): groq, openai, mistral...
    llm_model: str = "google/gemini-2.0-flash"
    llm_api_key: str = ""

    # Document storage
    download_dir: str = "downloads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
