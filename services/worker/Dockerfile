FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/worker/requirements.txt /app/services/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/services/worker/requirements.txt

COPY services/worker/app /app/services/worker/app
COPY migrations /app/migrations
COPY scripts /app/scripts
RUN chmod +x /app/scripts/*.sh

WORKDIR /app/services/worker
