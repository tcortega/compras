FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ingest /app/ingest
COPY normalize /app/normalize
COPY detect /app/detect
COPY infra /app/infra

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e /app/ingest

ENV PYTHONPATH=/app/ingest:/app/normalize:/app/detect \
    DAGSTER_HOME=/opt/dagster/home \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN mkdir -p /opt/dagster/home/compute_logs /opt/dagster/home/storage
COPY ingest/dagster.yaml /opt/dagster/home/dagster.yaml

WORKDIR /app
EXPOSE 3000
