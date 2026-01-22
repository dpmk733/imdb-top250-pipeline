import os
from dotenv import load_dotenv

import extract
import transform
import load


def _get_env_str(key, default):
    v = os.getenv(key)
    if v is None:
        return default
    v = v.strip()
    return default if v == "" else v


def _get_env_int(key, default):
    raw = os.getenv(key)
    if raw is None:
        return default
    raw = raw.strip()
    if raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def build_config():
    return {
        # DB
        "db_host": _get_env_str("DB_HOST", "db"),
        "db_port": _get_env_int("DB_PORT", 5432),
        "db_name": _get_env_str("DB_NAME", "imdb"),
        "db_user": _get_env_str("DB_USER", "postgres"),
        "db_password": _get_env_str("DB_PASSWORD", "postgres"),

        # Selenium
        "selenium_remote_url": _get_env_str("SELENIUM_REMOTE_URL", "http://selenium:4444/wd/hub"),

        # Scraping controls
        "imdb_top250_url": _get_env_str("IMDB_TOP250_URL", "https://www.imdb.com/chart/top/"),
        "top_n": _get_env_int("TOP_N", 250),
        "cast_top_n": _get_env_int("CAST_TOP_N", 10),
        "page_load_timeout": _get_env_int("PAGE_LOAD_TIMEOUT", 45),
        "wait_timeout": _get_env_int("WAIT_TIMEOUT", 30),
    }


def main():
    # Load .env for local runs; in Docker Compose the env vars are injected already.
    load_dotenv()

    cfg = build_config()

    # Create a run record (returns an integer run_id from Postgres)
    run_id = load.log_run_start(cfg)

    try:
        movies, cast = extract.run_extraction(
            selenium_remote_url=cfg["selenium_remote_url"],
            imdb_top250_url=cfg["imdb_top250_url"],
            top_n=cfg["top_n"],
            cast_top_n=cfg["cast_top_n"],
            page_load_timeout=cfg["page_load_timeout"],
            wait_timeout=cfg["wait_timeout"],
        )

        movies_df, cast_df = transform.transform(movies, cast)
        movies_rows, cast_rows = load.load(cfg, movies_df, cast_df)

        load.log_run_end(cfg, run_id, "SUCCESS", movies_rows, cast_rows, None)
        print(f"ETL run SUCCESS (run_id={run_id})")
        return 0

    except Exception as e:
        # No traceback module by design (simpler pipeline). We store only the exception message.
        error_message = str(e)
        print(f"ETL run FAILED (run_id={run_id}): {error_message}")
        load.log_run_end(cfg, run_id, "FAILED", 0, 0, error_message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
