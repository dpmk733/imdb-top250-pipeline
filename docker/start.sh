#!/bin/sh

# Copy cron jobs
crontab /app/cron_job

# Start cron in the background
cron

# Run ETL immediately when container starts
python /app/src/etl_pipeline.py

# Keep container alive
tail -f /var/log/cron.log
