#!/usr/bin/env bash


SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f $SCRIPT_DIR/../.env ]; then
    export $(grep -v '^#' $SCRIPT_DIR/../.env | xargs)
fi

DATA_FOLDER=${DATA_FOLDER:-./data}

mkdir -p ${DATA_FOLDER}/unfallatlas
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2016_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2016_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2017_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2017_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2018_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2018_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2019_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2019_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2020_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2020_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2021_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2021_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2022_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2022_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2023_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2023_EPSG25832_CSV.zip
wget -c https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2024_EPSG25832_CSV.zip -O ${DATA_FOLDER}/unfallatlas/Unfallorte2024_EPSG25832_CSV.zip