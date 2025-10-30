#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export $(grep -v '^#' .env | xargs)

NOMINATIM_STARTED_BY_SCRIPT=0

on_interrupt() {
    echo
    echo "Interrupt received. Stopping nominatim"
    if [ "$NOMINATIM_STARTED_BY_SCRIPT" -eq 1 ]; then
        "$SCRIPT_DIR/stop_nominatim.sh"
    fi
    exit 1
}
trap on_interrupt INT TERM

"$SCRIPT_DIR/start_nominatim.sh"
if [ $? -eq 0 ]; then
    NOMINATIM_STARTED_BY_SCRIPT=1
fi

poetry install
poetry run streamlit run schulkinder/app.py
