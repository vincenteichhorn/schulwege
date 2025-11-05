#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export $(grep -v '^#' .env | xargs)

NOMINATIM_STARTED_BY_SCRIPT=0
OTP_STARTED_BY_SCRIPT=0

on_interrupt() {
    echo
    echo "Interrupt received. Stopping"
    echo "Stopping Nominatim Service..."
    if [ "$NOMINATIM_STARTED_BY_SCRIPT" -eq 1 ]; then
        "$SCRIPT_DIR/stop_nominatim.sh"
    fi

    echo "Stopping OpenTripPlanner Service..."
    if [ "$OTP_STARTED_BY_SCRIPT" -eq 1 ]; then
        "$SCRIPT_DIR/stop_opentripplaner.sh"
    fi

    exit 1
}
trap on_interrupt INT TERM

"$SCRIPT_DIR/start_nominatim.sh"
if [ $? -eq 0 ]; then
    NOMINATIM_STARTED_BY_SCRIPT=1
fi
"$SCRIPT_DIR/start_opentripplaner.sh"
if [ $? -eq 0 ]; then
    OTP_STARTED_BY_SCRIPT=1
fi

poetry install
source $(poetry env info --path)/bin/activate
streamlit run schulkinder/app.py
