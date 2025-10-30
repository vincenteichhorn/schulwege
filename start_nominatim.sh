#!/bin/bash

export $(grep -v '^#' .env | xargs)

# container name should be ${NOMINATIM_BASE_CONTAINER_NAME}-region-with-dashes
# like nominatim-europe-germany-berlin if NOMINATIM_BASE_CONTAINER_NAME=nominatim and region=europe-germany-berlin
# the region is implicitly given in the NOMINATIM_REGION_PBF_URL like https://download.geofabrik.de/europe/germany/brandenburg-latest.osm.pbf

REGION=$(echo $NOMINATIM_REGION_PBF_URL | sed -E 's|https?://download\.geofabrik\.de/([^/]+)/([^/]+)/([^/]+)-latest\.osm\.pbf$|\1-\2-\3|' | tr ' ' '-' | tr '_' '-')
CONTAINER_NAME="${NOMINATIM_BASE_CONTAINER_NAME}-${REGION}"

echo "Starting Nominatim Service for region: $REGION"
echo "Using container name: $CONTAINER_NAME"

# flag to indicate we started/started an existing container in this script run
STARTED_BY_SCRIPT=0

# trap SIGINT/SIGTERM (Ctrl-C) and stop the container if we started it
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

# check if there is a docker container with that name already created
if [ "$(docker ps -a -q -f "name=^/${CONTAINER_NAME}$")" ]; then
    echo "Container $CONTAINER_NAME already exists. Starting existing container..."
    STARTED_BY_SCRIPT=1
    docker start "$CONTAINER_NAME"
else
    echo "Creating and starting new container $CONTAINER_NAME..."
    STARTED_BY_SCRIPT=1
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$NOMINATIM_HOST_PORT:$NOMINATIM_CONTAINER_PORT" \
        -v "$NOMINATIM_DATA_VOLUME:/var/lib/postgresql/12/main" \
        -v "$NOMINATIM_SETTINGS_VOLUME:/etc/nominatim" \
        -v "$NOMINATIM_FLATNODE_VOLUME:/var/lib/nominatim/flatnode" \
        -e "PBF_URL=$NOMINATIM_REGION_PBF_URL" \
        -e "NOMINATIM_PASSWORD=$NOMINATIM_PASSWORD" \
        "$NOMINATIM_IMAGE_NAME"
    echo "Nominatim server inside container $CONTAINER_NAME is starting and importing data from $NOMINATIM_REGION_PBF_URL. This may take a while (30min+) depending on the size of the data."
fi

echo "Waiting for Nominatim service to be fully started..."
spinner=('/' '-' '\' '|')
i=0
while true; do
    response=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" "http://localhost:$NOMINATIM_HOST_PORT/status.php")
    body=$(echo "$response" | sed -e 's/HTTPSTATUS\:.*//g')
    status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

    if [[ "$status" == "200" && "$body" == *"OK"* ]]; then
        echo
        break
    fi
    
    last_log_line=$(docker logs "$CONTAINER_NAME" 2>&1 | tail -n 1)
    spin_char=${spinner[i % ${#spinner[@]}]}
    echo -ne "\r[$spin_char] Log: $last_log_line"

    ((i++))
    sleep 1
done


echo "Nominatim service is up."