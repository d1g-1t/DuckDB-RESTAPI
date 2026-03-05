from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import CacheLayer
from app.config import settings
from app.engine import DuckDBEngine
from app.router import router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = DuckDBEngine(
        db_path=settings.db_path,
        memory_limit=settings.memory_limit,
        threads=settings.threads,
    )
    cache = CacheLayer(redis_url=settings.redis_url, ttl=settings.cache_ttl)
    await cache.connect()
    app.state.engine = engine
    app.state.cache = cache
    structlog.get_logger().info("started", port=8000)
    yield
    engine.close()
    await cache.close()


app = FastAPI(
    title="DuckDB REST API",
    description="Query anything. Cache everything. Stream the rest.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "DuckDB REST API",
        "version": "1.0.0",
        "docs": "/docs",
    }
