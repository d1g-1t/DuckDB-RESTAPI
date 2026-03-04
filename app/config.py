from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DUCKDB_API_"}

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600
    stream_chunk_size: int = 2000
    db_path: str = ":memory:"
    memory_limit: str = "512MB"
    threads: int = 4
    cors_origins: list[str] = ["*"]


settings = Settings()
