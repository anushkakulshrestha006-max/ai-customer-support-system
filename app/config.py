import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    """Application configuration settings loaded from environment variables."""

    # Project metadata
    PROJECT_NAME: str = "AI Customer Support System"
    VERSION: str = "1.0.0"

    # MySQL Configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "ai_customer_support")

    @property
    def DATABASE_URL(self) -> str:
        """Constructs MySQL SQLAlchemy connection string using pymysql driver."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    # LLM & AI Configuration
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")

    # Knowledge Base and Vector Index Paths
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "data" / "knowledge_base"
    FAISS_INDEX_DIR: Path = BASE_DIR / "data" / "faiss_index"

    # Backend Host Configuration
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8000))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


settings = Settings()
