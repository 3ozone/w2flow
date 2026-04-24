from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_debug: bool = False

    # Base de datos
    database_url: str

    # API contractaciopublica.cat
    licitation_api_base_url: str
    licitation_api_timeout: int = 30
    licitation_api_max_retries: int = 2

    # Notificaciones
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_recipients: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
