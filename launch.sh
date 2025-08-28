#!/usr/bin/env bash
set -euo pipefail

# Simple launcher for the Photo Trails Docker container with persistent data.
# You can override any of these via env vars before running the script.

IMAGE_NAME=${IMAGE_NAME:-photo-trails}
CONTAINER_NAME=${CONTAINER_NAME:-photo-trails}
PORT=${PORT:-8000}

# Host directory to persist DB and uploaded photos
PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DATA_DIR=${DATA_DIR:-"${PROJECT_DIR}/data"}

# Inside-container locations (do not change unless you modified the Dockerfile)
CONTAINER_DATA_DIR=/data
CONTAINER_DB_PATH=${CONTAINER_DB_PATH:-"${CONTAINER_DATA_DIR}/photo_trails.db"}
CONTAINER_PHOTOS_DIR=${CONTAINER_PHOTOS_DIR:-"${CONTAINER_DATA_DIR}/photos"}

echo "[photo-trails] Using data directory: ${DATA_DIR}"
mkdir -p "${DATA_DIR}/photos"

echo "[photo-trails] Building Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" "${PROJECT_DIR}"

echo "[photo-trails] Stopping any existing container: ${CONTAINER_NAME} (if running)"
docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

echo "[photo-trails] Starting container on port ${PORT}"
docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8000" \
  -v "${DATA_DIR}:${CONTAINER_DATA_DIR}" \
  -e PHOTO_TRAILS_DB="${CONTAINER_DB_PATH}" \
  -e PHOTO_DATA_DIR="${CONTAINER_PHOTOS_DIR}" \
  "${IMAGE_NAME}"

echo "[photo-trails] Container started. Open http://localhost:${PORT}"
echo "[photo-trails] Data persisted under: ${DATA_DIR}"
echo "[photo-trails] To view logs: docker logs -f ${CONTAINER_NAME}"
echo "[photo-trails] To stop: docker rm -f ${CONTAINER_NAME}"


