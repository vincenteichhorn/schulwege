# Schulwege

Schulwege is a Streamlit application that uses Nominatim for geocoding and
OpenTripPlanner (OTP) for public-transport routing. Docker Compose runs the
two supporting services and, optionally, the Streamlit frontend.

## Requirements

- Docker with the Compose plugin
- Poetry (development mode only)
- At least 8 GB of memory for the OTP build

## First-time setup

Clone the repository and create the environment file:

```bash
git clone https://github.com/vincenteichhorn/schulwege.git
cd schulwege
cp .env.example .env
```

Review `.env`, especially `REGION_PBF_URL` and `OTP_GTFS_URL`. The defaults
use Brandenburg, Germany and the VBB GTFS feed.

The following two commands are one-time data imports. They can take a long
time and only need to be repeated when the region or data source changes:

```bash
docker compose --profile build-nominatim up
docker compose --profile build-opentripplanner up \
  --abort-on-container-exit \
  --exit-code-from schulwege-opentripplanner-builder
```

For the Nominatim command, wait until the import has completed and then
press `Ctrl+C`; its service stays available for later starts.

The OTP build profile downloads the OSM PBF and GTFS files into
`data/opentripplanner` before running the builder. Existing files are reused,
so subsequent builds do not download them again.

## Start the application

After the initial data imports, start the complete application with one
command:

```bash
./scripts/start.sh
```

This builds the frontend image if needed and starts Nominatim, OTP, and
Streamlit. Open <http://localhost:5173>. Stop it with `Ctrl+C`.

## Development mode

Development mode runs Streamlit locally while Nominatim and OTP remain in
Docker. Install the Python dependencies once:

```bash
poetry install
```

Then start the supporting services and Streamlit with:

```bash
./scripts/start.sh dev
```

Open <http://localhost:5173>. The script stops the supporting containers when
Streamlit exits. Development mode uses the host ports configured in `.env`;
the normal container mode uses the Compose service names and internal ports.

## Configuration

All supported settings are documented in `.env.example`. The most relevant
ones are:

- `REGION_PBF_URL`: OSM extract used by Nominatim and OTP
- `OTP_GTFS_URL`: GTFS feed used by OTP
- `NOMINATIM_HOST_PORT`: host port for local Nominatim access
- `OTP_HOST_PORT`: host port for local OTP access
- `APP_PORT`: host port for Streamlit

To rebuild either imported dataset, stop the services and remove only the
corresponding directory under `data/`, then run its build profile again.

## Example address data

The file [`examples/babelsberg_adressen.csv`](examples/babelsberg_adressen.csv)
contains 50 example addresses around Babelsberg and the Stern district near
Schulzentrum am Stern. Upload it on the “Neues Projekt erstellen” page and
select the `address` column.
