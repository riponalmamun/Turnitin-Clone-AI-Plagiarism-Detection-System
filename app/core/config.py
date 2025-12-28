from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Turnitin Clone API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./storage/documents"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,doc"

    # AI APIs
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    GEMINI_API_KEY: Optional[str] = None

    # Search APIs
    SERPAPI_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    USE_DUCKDUCKGO: bool = True

    # Embeddings
    USE_LOCAL_EMBEDDINGS: bool = True
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"

    # Vector Database
    USE_VECTOR_DB: str = "chroma"
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Detection
    EXACT_MATCH_THRESHOLD: float = 90.0
    PARAPHRASE_THRESHOLD: float = 75.0
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.85
    MIN_MATCH_LENGTH: int = 8
    CHUNK_SIZE: int = 100
    OVERLAP: int = 20

    # API Strategy
    SEARCH_PRIORITY: str = "duckduckgo,serper,serpapi"
    AI_PRIORITY: str = "groq,gemini,openai"
    EMBEDDING_PRIORITY: str = "local,openai"

    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 50
    MAX_CONCURRENT_CHECKS: int = 3
    ENABLE_CACHING: bool = True
    CACHE_EXPIRY_HOURS: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_extensions_list(self) -> List[str]:
        return self.ALLOWED_EXTENSIONS.split(",")

    @property
    def search_priority_list(self) -> List[str]:
        return self.SEARCH_PRIORITY.split(",")

    @property
    def ai_priority_list(self) -> List[str]:
        return self.AI_PRIORITY.split(",")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()