# URL Shortener Service - Technical Design

## 1. Architecture Overview

The service uses Clean Architecture with four layers:

- Domain: Core entities and Base62 encoding logic.
- Application: URL shortening and resolving use cases.
- Infrastructure: PostgreSQL repository and Redis cache adapter.
- Presentation: FastAPI controllers, request/response schema validation, and HTTP error mapping.

Flow:

1. Client sends `POST /shorten` with `long_url`.
2. Service writes a new row to PostgreSQL and receives auto-incremented `id`.
3. `id` is converted to Base62 and saved as `short_code`.
4. Service returns `short_url`.
5. For `GET /{shortCode}`, the service checks Redis first, then PostgreSQL on cache miss, then redirects.

## 2. Database Schema and Indexing

DDL:

```sql
CREATE TABLE short_urls (
    id BIGSERIAL PRIMARY KEY,
    long_url TEXT NOT NULL,
    short_code VARCHAR(16) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_short_urls_short_code_unique ON short_urls (short_code);
CREATE INDEX idx_short_urls_created_at ON short_urls (created_at DESC);
```

Index strategy:

- `PRIMARY KEY (id)`: Fast writes and internal row identity.
- `UNIQUE (short_code)`: O(log n) lookup for redirect path and collision safety.
- `created_at DESC`: Efficient analytics/back-office time-window queries.

## 3. Scalability Plan for 10k+ RPS

### Read-through Caching with Redis

- Redirect traffic is read-heavy. Use Redis key/value:
  - key: `short_code`
  - value: `long_url`
- Request flow:
  1. Try Redis.
  2. On miss, read PostgreSQL.
  3. Populate Redis with TTL.

Expected effect:

- High cache hit ratio (80-95% for hot links) shifts load from DB to Redis.
- PostgreSQL handles durable writes and cold reads.

### Horizontal Scaling

- Stateless FastAPI app replicas behind L4/L7 load balancer.
- Shared PostgreSQL (primary + read replicas if needed) and Redis cluster.
- Connection pooling in app and PgBouncer in front of PostgreSQL.

### Capacity Guidance

- App tier: multiple instances with async workers.
- Redis: shard or cluster mode for memory scale.
- Database: partition by time or hash once table grows significantly.

## 4. Storage Estimation for 100 Million URLs

Assumptions per record:

- `id`: 8 bytes
- `short_code`: 8 bytes average (VARCHAR overhead omitted for simplicity)
- `created_at`: 8 bytes
- `long_url`: 200 bytes average
- Row + index overhead: ~60 bytes

Estimated row size:

$$
8 + 8 + 8 + 200 + 60 = 284 \text{ bytes}
$$

Total for 100,000,000 rows:

$$
284 \times 100,000,000 = 28,400,000,000 \text{ bytes} \approx 26.45 \text{ GiB}
$$

With growth headroom, bloat, backups, and replicas, provision at least:

- Primary DB storage: 80-120 GiB
- With one replica + WAL retention: 200+ GiB total cluster footprint

## 5. Collision Prevention in Distributed Environment

Current approach (single writer):

- `BIGSERIAL` guarantees unique IDs.
- Base62 encoding of unique ID guarantees unique `short_code`.
- Database unique index enforces safety.

Distributed-safe options:

1. Snowflake-style 64-bit IDs (timestamp + worker ID + sequence).
2. Hi/Lo ID blocks per instance to reduce central contention.
3. Dedicated ID generation service (e.g., etcd/Redis atomic counters).

Recommended strategy for production scale:

- Adopt Snowflake IDs per app instance.
- Encode Snowflake output using Base62.
- Keep DB unique index as final guardrail.

## 6. API Error Semantics

- `400 Bad Request`: invalid URL format for `POST /shorten`.
- `404 Not Found`: unknown short code for `GET /{shortCode}`.
- `301` or `302`: redirect behavior based on `permanent` query flag.

## 7. Reliability and Operations

- Structured logs with request IDs.
- Metrics: request count, latency, cache hit ratio, DB query latency.
- Alerts on 5xx spikes, Redis failures, and DB saturation.
- Nightly backups and tested restore process.
