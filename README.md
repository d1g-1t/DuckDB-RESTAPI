# DuckDB REST API

> DuckDB over HTTP. Query anything. Cache everything. Stream the rest.

Lightweight analytics API — send SQL, get JSON. Parquet, CSV, JSON, S3 — anything DuckDB can read becomes a queryable table. Repeated queries served from Redis in under 1ms. Large result sets streamed as NDJSON without blowing up memory.

## Quick Start

```bash
make setup
```

API → `http://localhost:9480` · Swagger UI → `http://localhost:9480/docs`

## API

### `POST /api/v1/query`

Execute SQL against DuckDB.

```bash
curl -s -X POST http://localhost:9480/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT department, AVG(salary) AS avg_sal FROM '\''data/sample.csv'\'' GROUP BY department"}'
```

```json
{
  "columns": ["department", "avg_sal"],
  "data": [["Engineering", 136625.0], ["Marketing", 96000.0], ["Product", 129600.0]],
  "row_count": 3,
  "cached": false,
  "execution_time_ms": 8.42
}
```

Request body:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sql` | string | *required* | Any SQL DuckDB supports |
| `stream` | bool | `false` | Return NDJSON stream instead of JSON |
| `no_cache` | bool | `false` | Bypass Redis cache |

### Stream mode

```bash
curl -s -X POST http://localhost:9480/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM range(1, 1000001) t(n)", "stream": true}'
```

Returns `application/x-ndjson` — one JSON object per line, streamed via async producer-consumer queue.

### `GET /api/v1/health`

```json
{"status": "ok", "duckdb": true, "redis": true}
```

### `DELETE /api/v1/cache`

Flush all cached query results.

## Architecture

```
POST /query → FastAPI → Cache check (Redis) → DuckDB → Response
                              ↓                    ↓
                         Cache hit → 1ms       Stream mode → NDJSON chunks
```

| Layer | What | Why |
|-------|------|-----|
| **DuckDB** | Analytical SQL engine | Reads Parquet, CSV, JSON, Excel, S3 natively |
| **Redis** | Query cache | blake2b fingerprint → sub-ms repeated queries |
| **Streaming** | NDJSON via async queue | Million-row results without OOM |
| **FastAPI + orjson** | HTTP layer | Async, fast serialization, OpenAPI docs free |

## Data Sources

Drop files into `data/` and query:

```sql
SELECT * FROM 'data/sales.parquet'
SELECT * FROM 'data/events.json'
SELECT * FROM 'data/report.csv' WHERE revenue > 1000
```

## Commands

| Command | What |
|---------|------|
| `make setup` | Build & start |
| `make down` | Stop |
| `make logs` | Tail API logs |
| `make test` | Run tests inside container |
| `make clean` | Nuke containers, volumes, images |
| `make status` | Container status |

## Configuration

All settings via environment variables (prefix `DUCKDB_API_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |
| `DB_PATH` | `:memory:` | DuckDB database path |
| `MEMORY_LIMIT` | `512MB` | DuckDB memory limit |
| `THREADS` | `4` | DuckDB threads |
| `STREAM_CHUNK_SIZE` | `2000` | Rows per stream chunk |

## Stack

Python 3.12 · FastAPI · DuckDB · Redis · Docker Compose · uv · orjson · structlog

## License

MIT
