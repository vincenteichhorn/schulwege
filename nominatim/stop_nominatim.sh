#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$SCRIPT_DIR/.."
export $(grep -v '^#' "$HOME_DIR/.env" | xargs)

REGION=$(echo $REGION_PBF_URL | sed -E 's|https?://download\.geofabrik\.de/([^/]+)/([^/]+)/([^/]+)-latest\.osm\.pbf$|\1-\2-\3|' | tr ' ' '-' | tr '_' '-')
CONTAINER_NAME="${NOMINATIM_BASE_CONTAINER_NAME}-${REGION}"

echo "Stopping Nominatim Service for region: $REGION"
echo "Using container name: $CONTAINER_NAME"

# Stop the container if it's running
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo "Stopping running container $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME
else
    echo "Container $CONTAINER_NAME is not running."
fi