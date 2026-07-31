from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://erp_user:erp_pass_2024@localhost:3307/erp_platform"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "erp-documents"
    minio_secure: bool = False

    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "erp_knowledge"

    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_default_model: str = "anthropic/claude-sonnet-4"
    llm_light_model: str = "deepseek/deepseek-v4-flash"

    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 1440

    wechat_corp_id: str = ""
    wechat_agent_id: str = ""
    wechat_secret: str = ""

    agent_config_dir: str = os.path.join(os.path.dirname(__file__), "..", "..", "config", "agents")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
