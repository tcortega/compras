#!/bin/sh
set -eu
mc alias set landing http://minio:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"
mc mb --ignore-existing landing/compras-landing
mc anonymous set none landing/compras-landing
echo "bucket compras-landing ready"
