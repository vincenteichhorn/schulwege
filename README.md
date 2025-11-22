# Schulwege

## Start Application Using Docker

### Download Data

```bash
./scripts/download_schools.sh
./scripts/download_ufa.sh
./scripts/download_otp.sh
```

### Build and Start Containers

To build the neccessary data for the application, run:

```bash
docker compose --profile build-nominatim up
```

Wait for the Nominatim data import to finish (e.g. log "[INFO] Application startup complete.") before proceeding to the next step.

Then, build the OpenTripPlanner data by running:

```bash
docker compose --profile build-opentripplanner up
```

To start all microservices, run:

```bash
docker compose --profile serve up
```

To start the application including the frontend, run:

```bash
docker compose --profile app up
```

## Setup Development Environment

Start the containers as described above, but do not start the profile "app". Then, install the dependencies and activate the virtual environment:

```bash
poetry install
source $(poetry env info --path)/bin/activate
schulwege
```
