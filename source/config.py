from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "HR Chatbot"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    OPENAI_API_KEY: str 
    OPENAI_LLM_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    QDRANT_URL: str = "http://localhost:6333"
    COLLECTION_NAME: str = "hr_policies_openai"

    MAX_CHAT_HISTORY_MESSAGES: int = 6 

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