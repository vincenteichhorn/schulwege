# Datengetriebene Schulwegeplanung
Durch die Allgemeine Verwaltungsvorschrift zur Straßenverkehrs-Ordnung (VwV-StVO) Novelle 2024/2025 ist es Kommunen ermöglicht Tempo 30 an hochfrequentierten Schulwegen anzuordnen. Dieses Projekt stellt eine datengetriebene Methode zur Identifikation und Priorisierung solcher Schulwege bereit. Das Identifizieren von hochfrequentierten Schulwegen kann auch Schulwegplänen erfolgen. Mit diesem Projekt können Schulen anhand der Adressen der Schüler:innen und der Lage der Schulen automatisch hochfrequentierte Schulwege identifizieren und entsprechend in ein Schulwegeplan einpflegen.

## Start Up Dev Environment
1. Install Docker on your machine.
2. Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/vincenteichhorn/schulwege.git
cd schulwege
```
3. This commands runs a development environment with hot-reloading for all backends and the streamlit app:
```bash
./dev.sh
```
5. Access the frontend application in your web browser at `http://localhost:5173`.

All details can be configured in the `.env` file. The provided `.env.example` file can be used as a template and is currently configured for Brandenburg, Germany.