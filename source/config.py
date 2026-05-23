from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "HR Chatbot"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    OPENAI_API_KEY: str
    OPENAI_LLM_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    QDRANT_URL: str
    COLLECTION_NAME: str = "hr_policies_openai"

    # Số tối đa turn hội thoại giữ lại (1 turn = user message + AI response + tool calls + tool results)
    # 6 turns ~ 24-30 messages
    MAX_CHAT_HISTORY_MESSAGES: int = 30
    API_USERNAME: str
    API_PASSWORD: str
    QDRANT_API_KEY: str
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Nếu trong .env có biến rác không khai báo ở đây thì tự động bỏ qua
    )

# Hàm get_settings sử dụng @lru_cache để đảm bảo class Settings 
# chỉ được khởi tạo 1 lần duy nhất trong suốt vòng đời của app (Singleton)
@lru_cache
def get_settings() -> Settings:
    return Settings()

# Biến settings này sẽ được import ở các file khác
settings = get_settings()
