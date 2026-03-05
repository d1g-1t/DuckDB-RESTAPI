from fastapi import Request

from app.cache import CacheLayer
from app.engine import DuckDBEngine


def get_engine(request: Request) -> DuckDBEngine:
    return request.app.state.engine


def get_cache(request: Request) -> CacheLayer:
    return request.app.state.cache
