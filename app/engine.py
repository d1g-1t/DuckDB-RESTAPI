import asyncio
from collections.abc import Iterator
from contextlib import contextmanager

import duckdb
import structlog

logger = structlog.get_logger()


class DuckDBEngine:
    def __init__(
        self,
        db_path: str = ":memory:",
        memory_limit: str = "512MB",
        threads: int = 4,
    ):
        self._db = duckdb.connect(db_path)
        self._configure(memory_limit, threads)

    def _configure(self, memory_limit: str, threads: int) -> None:
        self._db.execute(f"SET memory_limit = '{memory_limit}'")
        self._db.execute(f"SET threads = {threads}")

    @contextmanager
    def _cursor(self):
        conn = self._db.cursor()
        try:
            yield conn
        finally:
            conn.close()

    def new_cursor(self):
        return self._db.cursor()

    async def execute(self, sql: str) -> tuple[list[str], list[list]]:
        def _run():
            with self._cursor() as cur:
                result = cur.execute(sql)
                if result.description is None:
                    return [], []
                columns = [desc[0] for desc in result.description]
                rows = [list(row) for row in result.fetchall()]
                return columns, rows

        return await asyncio.to_thread(_run)

    def stream_sync(
        self, sql: str, chunk_size: int = 2000
    ) -> Iterator[tuple[list[str], list[tuple]]]:
        conn = self._db.cursor()
        try:
            result = conn.execute(sql)
            if result.description is None:
                return
            columns = [desc[0] for desc in result.description]
            while batch := result.fetchmany(chunk_size):
                yield columns, batch
        finally:
            conn.close()

    def health_check(self) -> bool:
        try:
            with self._cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False

    def close(self) -> None:
        self._db.close()
