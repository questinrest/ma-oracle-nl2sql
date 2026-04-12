import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("DB_PATH", "financials.db")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    llm_model: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    max_rows: int = int(os.getenv("MAX_ROWS", "200"))
    memory_search_limit: int = int(os.getenv("MEMORY_SEARCH_LIMIT", "4"))
    memory_type: str = os.getenv("MEMORY_TYPE", "demo")
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")


def get_settings() -> Settings:
    return Settings()

