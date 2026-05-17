from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    raw_data_dir: str = Field(default="", alias="RAW_DATA_DIR")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="", alias="QDRANT_COLLECTION")


@lru_cache
def get_settings():
    return Settings()
