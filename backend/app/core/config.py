from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReimagineDoomscrolling"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    lmstudio_base_url: str = "http://localhost:1234/v1"
    scheduler_enabled: bool = True
    scheduler_default_minutes: int = 60
    max_workers: int = 2
    temp_dir: str = "./tmp"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
