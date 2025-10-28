# Schulkinder Backend

## Setup Instructions

```bash
cd backend
poetry install
source $(poetry env info --path)/bin/activate

```

## Running the Backend Server
```bash
cd backend
export $(grep -v '^#' ../.env | xargs)
uvicorn src.api:api --reload --host 127.0.0.1 --port $BACKEND_PORT
```

