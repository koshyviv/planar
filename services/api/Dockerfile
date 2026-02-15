FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt

COPY services/api/app /app/services/api/app
COPY services/ui /app/services/ui
COPY migrations /app/migrations
COPY scripts /app/scripts
RUN chmod +x /app/scripts/*.sh

WORKDIR /app/services/api
