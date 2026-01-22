FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (cron for scheduling)
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Application code
COPY src /app/src
COPY docker/cron_job /app/docker/cron_job

# Create log dirs/files used by the container
RUN mkdir -p /app/data/logs \
    && touch /var/log/cron.log

# Start: install cron schedule, do one run now, then keep cron running and stream cron output
CMD ["sh", "-c", "crontab /app/docker/cron_job && echo '[container] Immediate ETL run...' && python /app/src/etl_pipeline.py || true; echo '[container] Starting cron...' && cron && tail -f /var/log/cron.log"]
