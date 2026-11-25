from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SmartCampus AI"
    env: str = "dev"
    database_url: str = "postgresql+psycopg://smartcampus:0000@localhost:5432/smartcampus_v2"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"
    embedding_dim: int = 768
    seed_team_password: str = ""  # dev only: creates one team account per role when set
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    # Session memory (temporary working memory of a conversation, see app/services/session_memory.py)
    session_ttl_minutes: int = 30  # idle expiry, extended at every message
    session_max_age_minutes: int = 240  # absolute lifetime, never extended
    session_max_turns: int = 6  # last N exchanges kept (user + assistant = 2 messages each)
    session_max_chars: int = 300  # characters kept per message
    session_max_bytes: int = 8192  # serialised size of one memory
    session_purge_interval_seconds: int = 300  # clean-up of expired memories
    # Optional LLM (existing Tunisian-Derja model, NOT fine-tuned here) behind any OpenAI-compatible endpoint (vLLM, Ollama...)
    # Chat without an account: nothing is stored, the state travels with the browser; these only bound abuse.
    guest_messages_per_minute: int = 20  # per IP address
    guest_max_state_bytes: int = 16384  # size of the state a visitor's browser may send back
    llm_enabled: bool = False
    llm_base_url: str = "http://localhost:8000/v1"
    llm_model: str = "ESPRIT-Group/ESPRIT-Derja-Qwen3-8B-v2"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 20.0
    llm_max_tokens: int = 400
    llm_temperature: float = 0.3
    llm_languages: str = "tn,arabizi"  # languages whose replies are rephrased by the LLM (French stays deterministic)

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
