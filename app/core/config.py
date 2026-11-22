from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SmartCampus AI"
    env: str = "dev"  # dev | test | prod — in dev the schema is created on startup
    database_url: str = "sqlite:///./smartcampus.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    embedding_dim: int = 768
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    password_min_length: int = 12

    # Demo data (accounts for every role, catalogue, candidates) inserted on startup when the database is empty.
    seed_demo_data: bool = False

    # Visitor (guest) chat sessions
    guest_idle_minutes: int = 30  # expires after this much inactivity…
    guest_max_hours: int = 24  # …and in any case this long after creation
    guest_max_messages: int = 40  # messages a visitor can send in one session
    guest_max_conversations: int = 3  # conversations per session
    guest_messages_per_minute: int = 8  # burst limit per session
    guest_sessions_per_hour_per_client: int = 20  # new sessions from the same network address
    guest_message_max_chars: int = 1000
    guest_purge_interval_minutes: int = 15  # background clean-up of expired sessions
    guest_retention_hours: int = 24  # expired, unclaimed sessions and their messages are deleted after this

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
