import asyncio
from collections.abc import AsyncIterator

import orjson

from app.engine import DuckDBEngine


async def ndjson_stream(
    engine: DuckDBEngine, sql: str, chunk_size: int = 2000
) -> AsyncIterator[bytes]:
    queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=16)
    loop = asyncio.get_running_loop()

    def _produce():
        try:
            for columns, batch in engine.stream_sync(sql, chunk_size):
                buf = b"".join(
                    orjson.dumps(dict(zip(columns, row)), default=str) + b"\n"
                    for row in batch
                )
                asyncio.run_coroutine_threadsafe(queue.put(buf), loop).result()
        except Exception as exc:
            error_line = orjson.dumps({"error": str(exc)}) + b"\n"
            asyncio.run_coroutine_threadsafe(queue.put(error_line), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

    loop.run_in_executor(None, _produce)

    while (chunk := await queue.get()) is not None:
        yield chunk
