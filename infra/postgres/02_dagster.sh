#!/bin/bash
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "SELECT 'CREATE DATABASE dagster' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dagster')\gexec"
