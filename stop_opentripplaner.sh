#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)

REGION=$(echo $REGION_PBF_URL | sed -E 's|https?://download\.geofabrik\.de/([^/]+)/([^/]+)/([^/]+)-latest\.osm\.pbf$|\1-\2-\3|' | tr ' ' '-' | tr '_' '-')
CONTAINER_NAME="${OTP_BASE_CONTAINER_NAME}-${REGION}"

echo "Stopping OpenTripPlanner Service for region: $REGION"
echo "Using container name: $CONTAINER_NAME"

# Stop the container if it's running
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Stopping running container $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
else
    echo "Container $CONTAINER_NAME is not running."
fi