FROM python:3.10-slim

# Create working directory
WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron && apt-get clean

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ETL source code
COPY src ./src

# Copy SQL scripts
COPY sql_scripts ./sql_scripts

# Copy data directory (logs etc.)
COPY data ./data

# Copy cron job definition
COPY docker/cron_job /app/cron_job

# Copy start script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# FIX: create cron log file
RUN touch /var/log/cron.log

# Default command (runs cron and ETL scheduler)
CMD ["sh", "/app/start.sh"]

