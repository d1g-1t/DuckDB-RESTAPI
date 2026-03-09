import time

import orjson
import structlog
from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import Response, StreamingResponse

from app.cache import CacheLayer
from app.config import settings
from app.deps import get_cache, get_engine
from app.engine import DuckDBEngine
from app.schemas import (
    CacheFlushResponse,
    HealthResponse,
    QueryRequest,
)
from app.streaming import ndjson_stream

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1")

_WRITE_PREFIXES = frozenset(
    {"INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "COPY", "EXPORT"}
)


def _is_read_query(sql: str) -> bool:
    first_token = sql.strip().split(maxsplit=1)[0].upper()
    return first_token not in _WRITE_PREFIXES


@router.post("/query")
async def query(
    req: QueryRequest,
    engine: DuckDBEngine = Depends(get_engine),
    cache: CacheLayer = Depends(get_cache),
):
    if req.stream:
        return StreamingResponse(
            ndjson_stream(engine, req.sql, settings.stream_chunk_size),
            media_type="application/x-ndjson",
        )

    is_read = _is_read_query(req.sql)

    if is_read and not req.no_cache:
        cached = await cache.get(req.sql)
        if cached is not None:
            cached["cached"] = True
            logger.info("cache_hit", sql=req.sql[:80])
            return Response(
                content=orjson.dumps(cached, default=str),
                media_type="application/json",
            )

    start = time.perf_counter()
    try:
        columns, rows = await engine.execute(req.sql)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    elapsed = round((time.perf_counter() - start) * 1000, 2)

    result = {
        "columns": columns,
        "data": rows,
        "row_count": len(rows),
        "cached": False,
        "execution_time_ms": elapsed,
    }

    if is_read and not req.no_cache:
        await cache.set(req.sql, result)

    logger.info("query_executed", rows=len(rows), time_ms=elapsed)
    return Response(
        content=orjson.dumps(result, default=str),
        media_type="application/json",
    )


@router.get("/health", response_model=HealthResponse)
async def health(
    engine: DuckDBEngine = Depends(get_engine),
    cache: CacheLayer = Depends(get_cache),
):
    return HealthResponse(
        status="ok",
        duckdb=engine.health_check(),
        redis=cache.available,
    )


@router.delete("/cache", response_model=CacheFlushResponse)
async def flush_cache(cache: CacheLayer = Depends(get_cache)):
    count = await cache.flush()
    return CacheFlushResponse(flushed_keys=count)
