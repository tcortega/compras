#!/bin/bash
set -euo pipefail
target="${DAGSTER_PG_DB:-dagster}"
exists="$(psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -tAc "SELECT 1 FROM pg_database WHERE datname = '${target}'")"
if [ "$exists" = "1" ]; then
  echo "database ${target} already exists"
  exit 0
fi
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "CREATE DATABASE ${target}"
echo "database ${target} created"
