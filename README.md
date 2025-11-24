# Schulwege

## Start Application

To start the application, clone the repository and navigate into the project directory. You need to have Docker and Docker Compose installed on your machine. The installation normally needs at minimum 45min, depending on your internet connection and hardware performance.

```bash
git clone https://github.com/vincenteichhorn/schulwege.git
cd schulwege
```

### Create Environment File

```bash
cp .env.example .env
```

Edit the `.env` file to set your desired configuration. You do not need to change anything if you are fine with the default settings. 
However, you should choose the `REGION_PBF_URL` that fits your area. For example, for Brandenburg, Germany, you can use:

```bash
REGION_PBF_URL=https://download.geofabrik.de/europe/germany/brandenburg-latest.osm.pbf
```

Set `DEV_MODE=1` if you want to run the application in development mode (optional).

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

To start all microservices, including the app:

```bash
docker compose --profile serve up
```

After the containers are started, you can access the frontend at `http://localhost:5173` (or the port you specified in the `.env` file).

## Setup Development Environment (Optional)

Start the containers as described above, but do not start the profile "app". Then, install the dependencies and activate the virtual environment:

```bash
poetry install
source $(poetry env info --path)/bin/activate
schulwege
```
