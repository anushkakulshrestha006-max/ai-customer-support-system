import os
import urllib.parse
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    """Application configuration settings loaded dynamically from environment variables."""

    def __init__(self):
        # Project metadata
        self.PROJECT_NAME: str = "AI Customer Support System"
        self.VERSION: str = "1.0.0"

        # Environment mode: development, production, test
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).strip().lower()

        # MySQL Configuration (supports DATABASE_URL, MYSQL_URL, MYSQL_PRIVATE_URL, and Railway MYSQLHOST)
        self._RAW_DATABASE_URL: str = (
            os.getenv("DATABASE_URL")
            or os.getenv("MYSQL_URL")
            or os.getenv("MYSQL_PRIVATE_URL")
            or ""
        ).strip()

        self.MYSQL_HOST: str = os.getenv("MYSQL_HOST") or os.getenv("MYSQLHOST") or "localhost"
        self.MYSQL_PORT: int = int(os.getenv("MYSQL_PORT") or os.getenv("MYSQLPORT") or 3306)
        self.MYSQL_USER: str = os.getenv("MYSQL_USER") or os.getenv("MYSQLUSER") or "root"
        self.MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD") or "root"
        self.MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE") or "ai_customer_support"

        # Connection pool configuration for hosted MySQL
        self.DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
        self.DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

        # LLM & AI Configuration
        self.LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")

        # Knowledge Base and Vector Index Paths
        self.KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "data" / "knowledge_base"
        self.FAISS_INDEX_DIR: Path = BASE_DIR / "data" / "faiss_index"

        # Backend Host Configuration (reads hosting platform PORT if provided)
        port_env = os.getenv("PORT")
        backend_port_env = os.getenv("BACKEND_PORT")
        self.BACKEND_PORT: int = int(port_env or backend_port_env or 8001)

        if port_env or self.ENVIRONMENT == "production":
            configured_host = os.getenv("BACKEND_HOST")
            self.BACKEND_HOST: str = configured_host if (configured_host and configured_host != "127.0.0.1") else "0.0.0.0"
        else:
            self.BACKEND_HOST: str = os.getenv("BACKEND_HOST", "127.0.0.1")

        self.BACKEND_URL: str = os.getenv("BACKEND_URL", f"http://127.0.0.1:{self.BACKEND_PORT}")


        # Security & Admin Protection
        self.ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")

        # CORS Configuration
        self.CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "")

    @property
    def DATABASE_URL(self) -> str:
        """
        Constructs or standardizes MySQL SQLAlchemy connection string.
        Safely URL-encodes user and password to handle special characters.
        Ensures pymysql dialect driver is specified.
        """
        if self._RAW_DATABASE_URL:
            raw = self._RAW_DATABASE_URL
            # Standardize mysql:// to mysql+pymysql://
            if raw.startswith("mysql://"):
                return raw.replace("mysql://", "mysql+pymysql://", 1)
            return raw

        encoded_user = urllib.parse.quote_plus(self.MYSQL_USER)
        encoded_pass = urllib.parse.quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_pass}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Returns allowed CORS origins as a list."""
        if self.CORS_ORIGINS_RAW.strip():
            return [orig.strip() for orig in self.CORS_ORIGINS_RAW.split(",") if orig.strip()]
        if self.ENVIRONMENT == "production":
            return [self.BACKEND_URL]
        return [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "*",
        ]

    def validate_production_settings(self) -> List[str]:
        """
        Validates configuration without leaking sensitive credentials.
        Returns a list of warning or error messages.
        """
        issues = []
        if self.ENVIRONMENT == "production":
            if not self._RAW_DATABASE_URL:
                if self.MYSQL_USER == "root":
                    issues.append("Production environment warning: Using 'root' database user. A restricted application user is recommended.")
                if self.MYSQL_PASSWORD in ("root", "", "password"):
                    issues.append("Production environment warning: Default or insecure database password detected.")
                if self.MYSQL_HOST in ("localhost", "127.0.0.1"):
                    issues.append("Production environment notice: MYSQL_HOST is set to localhost. Ensure hosted MySQL is configured.")
            if "127.0.0.1" in self.BACKEND_URL or "localhost" in self.BACKEND_URL:
                issues.append("Production environment notice: BACKEND_URL points to localhost. Ensure public URL is set for frontend communication.")
            if not self.ADMIN_API_KEY:
                issues.append("Production environment warning: ADMIN_API_KEY is not set. Ticket status updates are locked down until configured.")
        return issues


settings = Settings()
