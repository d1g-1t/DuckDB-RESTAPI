from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=100_000)
    stream: bool = False
    no_cache: bool = False


class QueryResponse(BaseModel):
    columns: list[str]
    data: list[list]
    row_count: int
    cached: bool
    execution_time_ms: float


class HealthResponse(BaseModel):
    status: str
    duckdb: bool
    redis: bool


class CacheFlushResponse(BaseModel):
    flushed_keys: int
