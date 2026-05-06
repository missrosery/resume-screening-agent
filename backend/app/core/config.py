from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    sync_database_url: str = Field(alias="SYNC_DATABASE_URL")
    dashscope_api_key: str = Field(alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="DASHSCOPE_BASE_URL",
    )
    llm_model: str = Field(default="qwen-plus", alias="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-v4", alias="EMBEDDING_MODEL")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_file_size: int = Field(default=10 * 1024 * 1024, alias="MAX_UPLOAD_FILE_SIZE")
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    vector_collection_name: str = Field(
        default="resume_documents",
        alias="VECTOR_COLLECTION_NAME",
    )
    vector_recall_k: int = Field(default=15, alias="VECTOR_RECALL_K")
    rerank_top_n: int = Field(default=5, alias="RERANK_TOP_N")
    agent_max_steps: int = Field(default=4, alias="AGENT_MAX_STEPS")

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
