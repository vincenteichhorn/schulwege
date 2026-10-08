#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

OTP_DATA_DIR="${OTP_DATA_DIR:-$PROJECT_DIR/data/opentripplanner}"
REGION_PBF_URL="${REGION_PBF_URL:?REGION_PBF_URL must be set}"
OTP_GTFS_URL="${OTP_GTFS_URL:?OTP_GTFS_URL must be set}"

mkdir -p "$OTP_DATA_DIR"
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
