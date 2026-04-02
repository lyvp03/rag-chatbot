from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ===== LLM =====
    LLM_API_KEY: str
    LLM_API_BASE: str
    LLM_MODEL: str = "GPT-5-mini"
    LLM_TEMPERATURE: float = 1.0

    # ===== Embedding =====
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_API_KEY: str
    EMBEDDING_API_URL: str

    # ===== Vector DB (FAISS) =====
    FAISS_PERSIST_DIR: str = "./faiss_data"

    # ===== File Upload =====
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # ===== Chunking =====
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # ===== Server =====
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # ===== Runtime helpers =====
    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def faiss_path(self) -> Path:
        path = Path(self.FAISS_PERSIST_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


settings = Settings()