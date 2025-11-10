#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export $(grep -v '^#' $SCRIPT_DIR/.env | xargs)

$SCRIPT_DIR/opentripplanner/download.sh

# if there is not graph.obj for OTP or no nominatim data (either files in the data dir of files in the flatnode dir have to exist, but not necessarily both), build them
if [ ! -f "${OTP_DATA_VOLUME}/graph.obj" ] || [ -z "$(ls -A ${NOMINATIM_DATA_VOLUME} 2>/dev/null)" ] && [ -z "$(ls -A ${NOMINATIM_FLATNODE_VOLUME} 2>/dev/null)" ]; then
  echo "Graph object not found, building..."
  docker compose --profile build up
fi

docker compose --profile serve up