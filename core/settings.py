from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略额外的环境变量
    )

    # Database
    database_url: str = Field("sqlite+aiosqlite:///./als.db", alias="DATABASE_URL")
    database_echo: bool = Field(False, alias="DATABASE_ECHO")

    # Vector DB
    vector_db_path: str = Field("./chroma_db", alias="VECTOR_DB_PATH")
    embedding_model: str = Field("all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    chroma_host: str = Field("localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(8000, alias="CHROMA_PORT")
    chroma_collection: str = Field("knowledge", alias="CHROMA_COLLECTION")
    chroma_persist_dir: str = Field("./chroma_data", alias="CHROMA_PERSIST_DIR")

    # LLM
    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field("gpt-3.5-turbo", alias="OPENAI_MODEL")
    llm_model: str = Field("gpt-3.5-turbo", alias="LLM_MODEL")
    llm_fallback_model: str = Field("gpt-3.5-turbo", alias="LLM_FALLBACK_MODEL")
    max_tokens: int = Field(2000, alias="MAX_TOKENS")
    temperature: float = Field(0.7, alias="TEMPERATURE")
    llm_max_retries: int = Field(3, alias="LLM_MAX_RETRIES")
    llm_timeout: int = Field(60, alias="LLM_TIMEOUT")
    llm_max_tokens: int = Field(4096, alias="LLM_MAX_TOKENS")

    # 讯飞 Spark API
    spark_appid: str = Field("", alias="SPARK_APPID")
    spark_api_key: str = Field("", alias="SPARK_API_KEY")
    spark_base_url: str = Field("https://spark-api-open.xf-yun.com/v1/chat/completions", alias="SPARK_BASE_URL")
    spark_model: str = Field("spark-lite", alias="SPARK_MODEL")

    # Background tasks
    task_interval_seconds: int = Field(60, alias="TASK_INTERVAL_SECONDS")
    exploration_interval_seconds: int = Field(3600, alias="EXPLORATION_INTERVAL_SECONDS")
    vector_sync_interval_seconds: int = Field(300, alias="VECTOR_SYNC_INTERVAL_SECONDS")

    # Vision profile
    vision_profile: str = Field("default", alias="VISION_PROFILE")

    # App
    app_name: str = Field("自主智能学习系统", alias="APP_NAME")
    debug: bool = Field(True, alias="DEBUG")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

settings = Settings()
