"""
Configuration centrale — backend/config.py
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    db_env: Literal["test", "production"] = "test"
    app_env: str = "development"
    log_level: str = "INFO"
    log_dir: str = "./logs"
    backend_port: int = 8000

    openai_api_key: str
    llm_model: str = "gpt-4o-mini"
    llm_model_fast: str = "gpt-4o-mini"
    max_tokens_nlp: int = 500
    max_tokens_sql: int = 800
    max_tokens_nlg: int = 600
    temperature_nlp: float = 0.1
    temperature_sql: float = 0.0
    temperature_nlg: float = 0.7

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "chatbot_db_test"
    db_user: str = "chatbot_user"
    db_password: str = ""
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout: int = 10
    db_pool_recycle: int = 3600

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 1800
    rate_limit_per_minute: int = 100

    secret_key: str = "dev-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    mcp_host: str = "127.0.0.1"
    mcp_port: int = 9000
    mcp_internal_key: str = ""

    bigdata_max_rows: int = 1000
    bigdata_timeout_sec: int = 10
    bigdata_partition_aware: bool = False

    @property
    def is_production(self) -> bool:
        return self.db_env == "production"

    @property
    def is_test(self) -> bool:
        return self.db_env == "test"

    @property
    def is_bigdata(self) -> bool:
        return self.db_env == "production"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    @property
    def mcp_base_url(self) -> str:
        return f"http://{self.mcp_host}:{self.mcp_port}"

    @property
    def effective_llm_model(self) -> str:
        if self.is_production:
            return "gpt-4o"
        return self.llm_model

    @property
    def sql_limit_max(self) -> int:
        return self.bigdata_max_rows if self.is_bigdata else 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()