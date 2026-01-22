# IMDb Selenium ETL Pipeline (Docker + Postgres)

This project scrapes the IMDb Top Rated list and top-billed cast (per title) using **Selenium** (remote Chrome), cleans the data, and upserts it into **Postgres** under the `analytics` schema.

The ETL also records each run in `analytics.etl_runs`. The `run_id` is an auto-incrementing integer (`BIGSERIAL`) so the Python code does not use UUIDs.

## Folder structure

```
imdb-selenium-pipeline/
├── .env
├── .gitignore
├── requirements.txt
├── data/
│   └── logs/
├── src/
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── etl_pipeline.py
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── cron_job
├── sql_scripts/
│   ├── init.sql
│   └── analysis.sql
└── documentation/
    ├── readme.md
    └── architecture.png
```

## What runs where

- `selenium` container: runs Chrome + Selenium server (Remote WebDriver)
- `db` container: Postgres 15, initializes tables from `sql_scripts/init.sql`
- `app` container: Python ETL code + cron scheduler

## How to run

From the project root folder:

```bash
# Build and start all services
docker compose -f docker/docker-compose.yml up -d --build

# Follow the app logs (stdout from print statements + cron output)
docker compose -f docker/docker-compose.yml logs -f app
```

### Run the ETL manually (inside the app container)

```bash
docker exec -it imdb_etl python /app/src/etl_pipeline.py
```

### Connect to Postgres and query

```bash
docker exec -it imdb_db psql -U postgres -d imdb

-- example queries
SELECT COUNT(*) FROM analytics.movies_top250;
SELECT COUNT(*) FROM analytics.movie_cast;

SELECT run_id, status, started_at, finished_at, movies_rows, cast_rows
FROM analytics.etl_runs
ORDER BY started_at DESC
LIMIT 5;
```

## Configuration (.env)

Edit `.env` to control:
- DB credentials (`POSTGRES_*`, `DB_*`)
- Selenium endpoint (`SELENIUM_REMOTE_URL`)
- scrape size (`TOP_N`, `CAST_TOP_N`)
- timeouts (`PAGE_LOAD_TIMEOUT`, `WAIT_TIMEOUT`)
- timezone (`TZ`) used by cron

## Notes

- The ETL uses **UPSERT** so re-running updates existing movies/cast.
- `TOP_N=50` and `CAST_TOP_N=5` are recommended for faster runs while testing.
- This version intentionally avoids Python `uuid`, `logging`, `typing`, and `traceback` to keep the code minimal.
