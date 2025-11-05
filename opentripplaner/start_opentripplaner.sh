#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="$SCRIPT_DIR/.."
export $(grep -v '^#' "$HOME_DIR/.env" | xargs)

# Derive region name from the PBF URL (like "europe-germany-brandenburg")
REGION=$(echo $REGION_PBF_URL | sed -E 's|https?://download\.geofabrik\.de/([^/]+)/([^/]+)/([^/]+)-latest\.osm\.pbf$|\1-\2-\3|' | tr ' ' '-' | tr '_' '-')
CONTAINER_NAME="${OTP_BASE_CONTAINER_NAME}-${REGION}"

echo "Starting OpenTripPlanner Service for region: $REGION"
echo "Using container name: $CONTAINER_NAME"

STARTED_BY_SCRIPT=0

# Handle Ctrl-C / termination
on_interrupt() {
    echo
    echo "Interrupt received. Stopping container $CONTAINER_NAME (if running and started by this script)..."
    if [ "$STARTED_BY_SCRIPT" -eq 1 ] && [ "$(docker ps -q -f "name=^/${CONTAINER_NAME}$")" ]; then
        docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
        echo "Container $CONTAINER_NAME stopped."
    fi
    exit 1
}
trap on_interrupt INT TERM

mkdir -p "$HOME_DIR/$OTP_DATA_VOLUME"

# Download OSM PBF if not exists
OSM_FILE="$HOME_DIR/$OTP_DATA_VOLUME/osm.pbf"
if [ ! -f "$OSM_FILE" ]; then
    echo "Downloading OSM PBF for $REGION..."
    curl -L "$REGION_PBF_URL" -o "$OSM_FILE"
else
    echo "OSM PBF already exists at $OSM_FILE, skipping download."
fi

# Download GTFS feed if not exists
GTFS_FILE="$HOME_DIR/$OTP_DATA_VOLUME/gtfs.zip"
if [ ! -f "$GTFS_FILE" ]; then
    echo "Downloading GTFS feed..."
    curl -L "$OTP_GTFS_URL" -o "$GTFS_FILE"
else
    echo "GTFS feed already exists at $GTFS_FILE, skipping download."
fi


# Check if container exists
if [ ! -f "$HOME_DIR/$OTP_DATA_VOLUME/graph.obj" ]; then
    echo "Creating and starting new container $CONTAINER_NAME..."
    STARTED_BY_SCRIPT=1
    
    echo "Building OTP graph from OSM and GTFS data..."
        docker run --rm \
            -e JAVA_TOOL_OPTIONS='-Xmx8g' \
            -v "$HOME_DIR/$OTP_DATA_VOLUME:/var/opentripplanner" \
            "$OTP_IMAGE_NAME" --build --save

    docker run -d --rm \
        --name "$CONTAINER_NAME" \
        -e JAVA_TOOL_OPTIONS='-Xmx8g' \
        -p "$OTP_HOST_PORT:$OTP_CONTAINER_PORT" \
        -v "$HOME_DIR/$OTP_DATA_VOLUME:/var/opentripplanner" \
        "$OTP_IMAGE_NAME" --load --serve
else

    echo "Graph $CONTAINER_NAME exists. Using existing graph for new container..."
    STARTED_BY_SCRIPT=1
    docker run -d --rm \
        --name "$CONTAINER_NAME" \
        -e JAVA_TOOL_OPTIONS='-Xmx8g' \
        -p "$OTP_HOST_PORT:$OTP_CONTAINER_PORT" \
        -v "$HOME_DIR/$OTP_DATA_VOLUME:/var/opentripplanner" \
        "$OTP_IMAGE_NAME" --load --serve

    echo "OTP container $CONTAINER_NAME is starting..."
fi

echo "Waiting for OTP service to be fully started..."
spinner=('/' '-' '\' '|')
i=0
while true; do
    # Simple health check via the router API
    response=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" "http://localhost:$OTP_HOST_PORT")
    status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

    if [[ "$status" == "200" ]]; then
        echo
        break
    fi
    
    last_log_line=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -n 1)
    spin_char=${spinner[i % ${#spinner[@]}]}
    echo -ne "\r[$spin_char] Log: $last_log_line"

    ((i++))
    sleep 1
done

echo "OpenTripPlanner service is up and running at http://localhost:$OTP_HOST_PORT"