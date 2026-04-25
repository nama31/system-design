CREATE TABLE IF NOT EXISTS short_urls (
    id BIGSERIAL PRIMARY KEY,
    long_url TEXT NOT NULL,
    short_code VARCHAR(16) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_short_urls_short_code_unique ON short_urls (short_code);
CREATE INDEX IF NOT EXISTS idx_short_urls_created_at ON short_urls (created_at DESC);
