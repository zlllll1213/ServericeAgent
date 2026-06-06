from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "serviceflow.db"
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

    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore", populate_by_name=True)


settings = Settings()
