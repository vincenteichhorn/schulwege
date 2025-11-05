# Datengetriebene Schulwegeplanung
Durch die Allgemeine Verwaltungsvorschrift zur Straßenverkehrs-Ordnung (VwV-StVO) Novelle 2024/2025 ist es Kommunen ermöglicht Tempo 30 an hochfrequentierten Schulwegen anzuordnen. Dieses Projekt stellt eine datengetriebene Methode zur Identifikation und Priorisierung solcher Schulwege bereit. Das Identifizieren von hochfrequentierten Schulwegen kann auch Schulwegplänen erfolgen. Mit diesem Projekt können Schulen anhand der Adressen der Schüler:innen und der Lage der Schulen automatisch hochfrequentierte Schulwege identifizieren und entsprechend in ein Schulwegeplan einpflegen.

Da die Adressen der Schüler:innen sensible personenbezogene Daten sind, verwendet dieses Projekt keine externen API-Dienste. Stattdessen werden alle Berechnungen lokal durchgeführt, um die Privatsphäre der Schüler:innen zu schützen. Importierte Adressdaten werden in einer lokalen Datenbank gespeichert und verarbeitet.

## Routing
Das Projekt verwendet um die Schulwege zu berechnen Routing mit kürzesten Wegen basierend auf OpenStreetMap-Daten für Lauf- und Fahrradwege. Für ÖPNV-Routing wird das Open-Source-Tool OpenTripPlanner verwendet, das lokal betrieben wird. 

## Gebiete
Entsprechend sind PBF-Daten und GTFS-Daten für das jeweilige Gebiet erforderlich. Diese können in der `.env` Datei konfiguriert werden. Beispielkonfigurationen für verschiedene Gebiete sind unten aufgeführt.
### Brandenburg/Berlin
```
REGION_PBF_URL=https://download.geofabrik.de/europe/germany/brandenburg-latest.osm.pbf
OTP_GTFS_URL=https://vbb.de/vbbgtfs
```

## Start Up Dev Environment
1. Install Docker on your machine.
2. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/vincenteichhorn/schulwege.git
cd schulwege
```
3. This commands runs a development environment with hot-reloading for all backends and the streamlit app. The first time you run it, it will download necessary data and build the environment, which may take some time (~30-60 minutes).
```bash
./dev.sh
```
5. Access the frontend application in your web browser at `http://localhost:5173`.

All details can be configured in the `.env` file. The provided `.env.example` file can be used as a template and is currently configured for Brandenburg, Germany.