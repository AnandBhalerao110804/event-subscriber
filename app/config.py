from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    admin_api_key: str = "dev-admin-key"
    database_path: str = "data/webhooks.db"
    worker_poll_interval_sec: float = 2.0
    delivery_timeout_sec: float = 10.0
    max_delivery_attempts: int = 5
    retry_base_delay_sec: float = 1.0
    retry_max_delay_sec: float = 60.0
    stale_delivering_sec: int = 120


settings = Settings()
