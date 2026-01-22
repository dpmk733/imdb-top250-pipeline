# IMDb Top List ETL (Selenium + Postgres)

This project scrapes the IMDb Top chart with Selenium, cleans the data, and loads it into Postgres. Everything runs in Docker.

## What it loads

- `analytics.movies_top250`  
  Movie rows from the IMDb Top chart (rank/title/year/rating/imdb_id/url).

- `analytics.movie_cast`  
  Cast rows per movie (movie imdb_id + cast name + order).

- `analytics.etl_runs`  
  A simple run log table (start/end/status/row counts).

## Folder structure

```
.
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

## Requirements

- Docker + Docker Compose
- (Windows) WSL2 recommended

## Setup

Create `.env` in the project root. Example:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=imdb

DB_HOST=db
DB_PORT=5432
DB_NAME=imdb
DB_USER=postgres
DB_PASSWORD=postgres

SELENIUM_REMOTE_URL=http://selenium:4444/wd/hub

TOP_N=50
CAST_TOP_N=5
PAGE_LOAD_TIMEOUT=45
WAIT_TIMEOUT=30

TZ=Europe/Athens
```

If you plan to push this to GitHub, don’t commit real secrets. Keep `.env` ignored and commit an `.env.example` instead.

## Run

Compose file is inside `docker/`, so run it using `-f` and pass the env file explicitly:

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
```

Follow logs:

```bash
docker compose --env-file .env -f docker/docker-compose.yml logs -f app
```

Stop:

```bash
docker compose --env-file .env -f docker/docker-compose.yml down
```

Reset DB (drops the volume too):

```bash
docker compose --env-file .env -f docker/docker-compose.yml down -v
```

## Check data in Postgres

Open psql inside the container:

```bash
docker exec -it imdb_db psql -U postgres -d imdb
```

Basic checks:

```sql
SELECT COUNT(*) AS movies FROM analytics.movies_top250;
SELECT COUNT(*) AS cast_rows FROM analytics.movie_cast;

SELECT run_id, status, started_at, finished_at, movies_rows, cast_rows
FROM analytics.etl_runs
ORDER BY started_at DESC
LIMIT 5;
```

## Cron schedule

Cron config is in:

- `docker/cron_job`

If you change the schedule, recreate the app container:

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d --build --force-recreate
```

## Notes / common issues

### Env values not applied

Verify what the container sees:

```bash
docker exec -it imdb_etl sh -lc 'echo TOP_N=$TOP_N; echo CAST_TOP_N=$CAST_TOP_N'
```

If you edited `.env`, recreate the container:

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d --build --force-recreate
```

### Tables not created

`init.sql` runs only on a fresh DB volume. If you need a clean DB:

```bash
docker compose --env-file .env -f docker/docker-compose.yml down -v
docker compose --env-file .env -f docker/docker-compose.yml up -d --build
```

## License

See `LICENSE`.
