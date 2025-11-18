#!/usr/bin/env bash


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f $SCRIPT_DIR/../.env ]; then
    export $(grep -v '^#' $SCRIPT_DIR/../.env | xargs)
fi

mkdir -p "$OTP_DATA_DIR"
chmod -R 777 "$OTP_DATA_DIR"
OSM_FILE="$OTP_DATA_DIR/osm.pbf"
GTFS_FILE="$OTP_DATA_DIR/gtfs.zip"


if [ ! -f "$OSM_FILE" ]; then
  echo "Downloading OSM PBF from $REGION_PBF_URL..."
  wget -L "$REGION_PBF_URL" -O "$OSM_FILE"
else
  echo "OSM PBF already exists, skipping download."
fi

if [ ! -f "$GTFS_FILE" ]; then
  echo "Downloading GTFS feed from $OTP_GTFS_URL..."
  wget -L "$OTP_GTFS_URL" -O "$GTFS_FILE"
else
  echo "GTFS feed already exists, skipping download."
fi
