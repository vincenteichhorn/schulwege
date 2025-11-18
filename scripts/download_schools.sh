#!/usr/bin/env bash


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f $SCRIPT_DIR/../.env ]; then
    export $(grep -v '^#' $SCRIPT_DIR/../.env | xargs)
fi

DATA_FOLDER=${DATA_FOLDER:-./data}

mkdir -p ${DATA_FOLDER}/schools
wget -c "https://opendata.potsdam.de/api/explore/v2.1/catalog/datasets/schulen/exports/csv?lang=de&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B" -O ${DATA_FOLDER}/schools/schulen_potsdam.csv