from datetime import datetime, timezone

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


UPSERT_MOVIES_SQL = """
INSERT INTO analytics.movies_top250 (imdb_id, rank, title, release_year, rating, imdb_url, scraped_at)
VALUES %s
ON CONFLICT (imdb_id) DO UPDATE SET
    rank = EXCLUDED.rank,
    title = EXCLUDED.title,
    release_year = EXCLUDED.release_year,
    rating = EXCLUDED.rating,
    imdb_url = EXCLUDED.imdb_url,
    scraped_at = EXCLUDED.scraped_at;
"""

UPSERT_CAST_SQL = """
INSERT INTO analytics.movie_cast (imdb_id, cast_order, actor_name, character_name, actor_url, scraped_at)
VALUES %s
ON CONFLICT (imdb_id, cast_order) DO UPDATE SET
    actor_name = EXCLUDED.actor_name,
    character_name = EXCLUDED.character_name,
    actor_url = EXCLUDED.actor_url,
    scraped_at = EXCLUDED.scraped_at;
"""

INSERT_RUN_SQL = """
INSERT INTO analytics.etl_runs (started_at, status, movies_rows, cast_rows, error_message)
VALUES (%s, %s, %s, %s, %s)
RETURNING run_id;
"""

UPDATE_RUN_SQL = """
UPDATE analytics.etl_runs
SET finished_at=%s, status=%s, movies_rows=%s, cast_rows=%s, error_message=%s
WHERE run_id=%s;
"""



def _connect(cfg):
    """Create a Postgres connection using values from cfg."""
    return psycopg2.connect(
        host=cfg["db_host"],
        port=cfg["db_port"],
        dbname=cfg["db_name"],
        user=cfg["db_user"],
        password=cfg["db_password"],
    )


def _bulk_upsert(cur, sql, rows, page_size=500):
    rows_list = list(rows)
    if not rows_list:
        return 0
    execute_values(cur, sql, rows_list, page_size=page_size)
    return len(rows_list)


def load(cfg, movies_df, cast_df):
    """Upsert movies + cast into Postgres. Returns (movies_rows, cast_rows) loaded."""
    scraped_at = datetime.now(timezone.utc)

    movie_rows = []
    if not movies_df.empty:
        for r in movies_df.itertuples(index=False):
            movie_rows.append(
                (
                    str(r.imdb_id),
                    int(r.rank) if r.rank is not None else None,
                    str(r.title),
                    int(r.release_year) if r.release_year is not None else None,
                    float(r.rating) if r.rating is not None and pd.notna(r.rating) else None,
                    str(r.imdb_url),
                    scraped_at,
                )
            )

    cast_rows = []
    if not cast_df.empty:
        for r in cast_df.itertuples(index=False):
            cast_rows.append(
                (
                    str(r.imdb_id),
                    int(r.cast_order) if r.cast_order is not None else None,
                    str(r.actor_name),
                    None if pd.isna(r.character_name) else str(r.character_name),
                    None if pd.isna(r.actor_url) else str(r.actor_url),
                    scraped_at,
                )
            )

    conn = _connect(cfg)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            m_cnt = _bulk_upsert(cur, UPSERT_MOVIES_SQL, movie_rows)
            c_cnt = _bulk_upsert(cur, UPSERT_CAST_SQL, cast_rows)
        conn.commit()
        print(f"[load] Loaded: movies={m_cnt}, cast={c_cnt}")
        return m_cnt, c_cnt
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_run_start(cfg):
    """Insert a RUNNING row into analytics.etl_runs. Returns integer run_id."""
    now = datetime.now(timezone.utc)
    conn = _connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(INSERT_RUN_SQL, (now, "RUNNING", 0, 0, None))
            run_id = cur.fetchone()[0]
        conn.commit()
        return run_id
    finally:
        conn.close()


def log_run_end(cfg, run_id, status, movies_rows, cast_rows, error_message):
    """Update analytics.etl_runs with completion status and row counts."""
    now = datetime.now(timezone.utc)
    conn = _connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(UPDATE_RUN_SQL, (now, status, movies_rows, cast_rows, error_message, run_id))
        conn.commit()
    finally:
        conn.close()
