-- schemas
CREATE SCHEMA IF NOT EXISTS analytics;

-- ETL run log (one row per run)
-- run_id is BIGSERIAL to avoid UUID usage in Python.
CREATE TABLE IF NOT EXISTS analytics.etl_runs (
    run_id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    movies_rows INTEGER DEFAULT 0,
    cast_rows INTEGER DEFAULT 0,
    error_message TEXT
);

-- Top 250 movies (current snapshot; updated on each run)
CREATE TABLE IF NOT EXISTS analytics.movies_top250 (
    imdb_id TEXT PRIMARY KEY,
    rank INTEGER NOT NULL,
    title TEXT NOT NULL,
    release_year INTEGER,
    rating NUMERIC(3,1),
    imdb_url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_movies_top250_rank ON analytics.movies_top250(rank);

-- Cast for each title (top N cast members per movie; upsert by (imdb_id, cast_order))
CREATE TABLE IF NOT EXISTS analytics.movie_cast (
    imdb_id TEXT NOT NULL REFERENCES analytics.movies_top250(imdb_id) ON DELETE CASCADE,
    cast_order INTEGER NOT NULL,
    actor_name TEXT NOT NULL,
    character_name TEXT,
    actor_url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (imdb_id, cast_order)
);

CREATE INDEX IF NOT EXISTS idx_movie_cast_imdb_id ON analytics.movie_cast(imdb_id);
