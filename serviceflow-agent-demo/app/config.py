import os
from pathlib import Path
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = Path(os.environ.get("SERVICEFLOW_DB_PATH", DATA_DIR / "serviceflow.db"))
KNOWLEDGE_BASE_DIR = ROOT_DIR / "knowledge_base"


class Settings(BaseSettings):
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    qdrant_url: str = Field(default="http://127.0.0.1:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="serviceflow_knowledge", alias="QDRANT_COLLECTION")
    qdrant_vector_size: int = Field(default=384, alias="QDRANT_VECTOR_SIZE")
    qdrant_enabled: bool = Field(default=True, alias="QDRANT_ENABLED")
    qdrant_timeout_seconds: float = Field(default=3.0, alias="QDRANT_TIMEOUT_SECONDS")
    auth_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), alias="AUTH_SECRET")
    auth_issuer: str = Field(default="serviceflow-agent-demo", alias="AUTH_ISSUER")
    auth_audience: str = Field(default="serviceflow-admin", alias="AUTH_AUDIENCE")
    auth_token_ttl_seconds: int = Field(default=3600, alias="AUTH_TOKEN_TTL_SECONDS")
    demo_auth_enabled: bool = Field(default=False, alias="DEMO_AUTH_ENABLED")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password_hash: str | None = Field(default=None, alias="ADMIN_PASSWORD_HASH")
    agent_username: str = Field(default="service_agent", alias="AGENT_USERNAME")
    agent_password_hash: str | None = Field(default=None, alias="AGENT_PASSWORD_HASH")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    rate_limit_backend: str = Field(default="memory", alias="RATE_LIMIT_BACKEND")
    chat_rate_limit_enabled: bool = Field(default=True, alias="CHAT_RATE_LIMIT_ENABLED")
    chat_rate_limit_requests: int = Field(default=60, alias="CHAT_RATE_LIMIT_REQUESTS")
    chat_rate_limit_window_seconds: int = Field(default=60, alias="CHAT_RATE_LIMIT_WINDOW_SECONDS")
    clarify_confidence_threshold: float = Field(default=0.45, alias="CLARIFY_CONFIDENCE_THRESHOLD")
    intent_conflict_high_confidence_threshold: float = Field(default=0.7, alias="INTENT_CONFLICT_HIGH_CONFIDENCE_THRESHOLD")
    intent_conflict_confidence_gap: float = Field(default=0.12, alias="INTENT_CONFLICT_CONFIDENCE_GAP")

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore", populate_by_name=True)


settings = Settings()
