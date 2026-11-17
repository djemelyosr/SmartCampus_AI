from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SmartCampus AI"
    env: str = "dev"
    database_url: str = "sqlite:///./smartcampus.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    embedding_dim: int = 768
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
